"""StudySprint AI — single-page Streamlit app.

Slice 5: the student answers the five questions and clicks Submit Answers.
Valid submissions are graded in Python and show the score, correct answers with
explanations, and weak topics; unanswered submissions are blocked. Revision
scheduling and Start Over are not wired up yet.
"""

import logging
import os
import traceback
from datetime import date, timedelta

import streamlit as st

import ai_client
import quiz_logic
import validators

LOGGER = logging.getLogger(__name__)

QUIZ_ERROR = "We couldn't build your quiz right now. Please try again in a moment."
SCHEMA_ERROR = "We couldn't build a usable quiz from those notes. Please try again."
SUBMIT_ERROR = "Please answer all five questions before submitting."
POSITIVE_RESULT = "Great work! No weak topics were identified in this quiz."
HINT = (
    "Your personalized quiz, results, and revision plan will appear here "
    "after you generate your quiz."
)

st.set_page_config(page_title="StudySprint AI", layout="centered")

st.title("StudySprint AI")
st.write(
    "Turn your study notes into a focused quiz and a personalized revision plan."
)


def _show_error(field):
    """Render the stored validation message for one field, if there is one.

    Messages are stored by the button callback just before the page re-runs, so
    each one can appear right under its own field.
    """
    message = st.session_state.get("errors", {}).get(field)
    if message:
        st.error(message)


def _on_generate():
    """Validate the inputs, then queue a Gemini call if everything is valid.

    Runs as the button callback, before the page re-runs, so the inline messages
    are ready when the fields render. No AI call happens while inputs are
    invalid, and any previous quiz, answers, and results are cleared first.
    """
    st.session_state["ui_error"] = None
    st.session_state["errors"] = validators.validate_inputs(
        st.session_state.get("notes", ""),
        st.session_state.get("exam_date"),
        st.session_state.get("hours"),
        date.today(),
    )
    if not st.session_state["errors"]:
        st.session_state["quiz"] = None
        st.session_state["generate_pending"] = True
        for key in ("submitted", "score", "per_question", "weak_topics"):
            st.session_state.pop(key, None)
        for number in range(1, quiz_logic.QUESTIONS_PER_QUIZ + 1):
            st.session_state.pop(f"answer_{number}", None)


def _log_failure():
    """Write the real failure to the Streamlit server terminal, with no secrets.

    The browser only ever sees the generic `QUIZ_ERROR`, so the exception type
    and traceback are logged here. Any API key value present in the traceback is
    redacted before logging, and neither `.env` contents nor request headers are
    ever read or printed.
    """
    detail = traceback.format_exc()
    for name in ("GEMINI_API_KEY", "GOOGLE_API_KEY"):
        value = os.environ.get(name)
        if value:
            detail = detail.replace(value, "[redacted]")
    LOGGER.error("Quiz generation failed:\n%s", detail)


def _generate_quiz():
    """Call Gemini, validate the result, and store the quiz or a friendly error."""
    notes = st.session_state.get("notes", "")
    try:
        raw = ai_client.generate_quiz(notes)
    except ai_client.AiError:
        _log_failure()
        st.session_state["ui_error"] = QUIZ_ERROR
        return

    ok, result = quiz_logic.validate_quiz(raw)
    if not ok:
        LOGGER.error("Quiz schema validation rejected the response: %s", result)
        st.session_state["ui_error"] = SCHEMA_ERROR
        return

    st.session_state["quiz"] = result
    st.session_state["ui_error"] = None


def _selected_answers():
    """Return the stored radio selections as option indices.

    Each `st.radio` stores the chosen option string under `answer_<n>`, so it is
    mapped back to its index in that question's options list. An unanswered
    question stays `None`, which `quiz_logic.grade_quiz` treats as wrong.
    """
    answers = []
    for number, question in enumerate(st.session_state.get("quiz") or [], start=1):
        selected = st.session_state.get(f"answer_{number}")
        if selected is None:
            answers.append(None)
        else:
            answers.append(question["options"].index(selected))
    return answers


def _on_submit():
    """Grade the stored answers, or block with a message if any are missing.

    Runs as the button callback, before the page re-runs. Grading happens exactly
    once per click; ordinary reruns only read the stored results.
    """
    quiz = st.session_state.get("quiz")
    if not quiz:
        return
    answers = _selected_answers()
    if any(answer is None for answer in answers):
        st.session_state["ui_error"] = SUBMIT_ERROR
        return
    score, per_question = quiz_logic.grade_quiz(quiz, answers)
    st.session_state["score"] = score
    st.session_state["per_question"] = per_question
    st.session_state["weak_topics"] = quiz_logic.find_weak_topics(quiz, per_question)
    st.session_state["submitted"] = True
    st.session_state["ui_error"] = None


def _render_quiz(quiz):
    """Show the five questions as radio groups — never the answers or explanations."""
    st.subheader("Your quiz")
    if st.session_state.get("submitted"):
        st.caption("Your answers are locked.")
    else:
        st.caption("Choose one option for each question. Nothing is graded yet.")
    for number, question in enumerate(quiz, start=1):
        with st.container(border=True):
            st.markdown(f"**{number}. {question['question']}**")
            st.caption(question["topic"])
            st.radio(
                f"Question {number}",
                options=question["options"],
                index=None,
                key=f"answer_{number}",
                label_visibility="collapsed",
                disabled=st.session_state.get("submitted", False),
            )


def _render_results(quiz):
    """Show the score, per-question feedback, and weak topics after submission."""
    st.subheader("Your results")
    st.markdown(f"**Score: {st.session_state['score']} / {len(quiz)}**")

    for number, (question, result) in enumerate(
        zip(quiz, st.session_state["per_question"]), start=1
    ):
        with st.container(border=True):
            mark = "Correct" if result["correct"] else "Incorrect"
            st.markdown(f"**{number}. {question['question']}** — {mark}")
            st.caption(question["topic"])
            if not result["correct"]:
                st.write(f"Your answer: {question['options'][result['selected_index']]}")
            st.write(f"Correct answer: {question['options'][result['correct_index']]}")
            st.write(question["explanation"])

    weak_topics = st.session_state["weak_topics"]
    if weak_topics:
        st.subheader("Weak topics")
        for item in weak_topics:
            st.write(f"**{item['topic']}** — {item['mistakes']} mistake(s)")
    else:
        st.success(POSITIVE_RESULT)


with st.container(border=True):
    st.text_area(
        "Study notes",
        height=220,
        key="notes",
        placeholder="Paste your study notes here...",
    )
    _show_error("notes")

    left, right = st.columns(2)
    with left:
        st.date_input(
            "Exam date",
            value=date.today() + timedelta(days=1),
            key="exam_date",
        )
        _show_error("exam_date")
    with right:
        st.number_input(
            "Daily study hours",
            value=2.0,
            step=0.5,
            key="hours",
        )
        _show_error("hours")

    st.button(
        "Generate Quiz",
        type="primary",
        key="generate",
        on_click=_on_generate,
        disabled=st.session_state.get("generate_pending", False),
    )

if st.session_state.get("generate_pending", False):
    with st.spinner("Generating your quiz..."):
        try:
            _generate_quiz()
        finally:
            st.session_state["generate_pending"] = False

ui_error = st.session_state.get("ui_error")
quiz = st.session_state.get("quiz")

if ui_error:
    st.error(ui_error)

if quiz:
    _render_quiz(quiz)
    if st.session_state.get("submitted"):
        _render_results(quiz)
    else:
        st.button("Submit Answers", type="primary", key="submit", on_click=_on_submit)
elif not ui_error:
    st.info(HINT)
