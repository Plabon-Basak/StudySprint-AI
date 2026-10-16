"""StudySprint AI — single-page Streamlit app.

Slice 5: the student answers the five questions and clicks Submit Answers.
Valid submissions are graded in Python and show the score, correct answers with
explanations, weak topics, and a day-by-day revision schedule; unanswered
submissions are blocked. Start Over returns the whole run to its initial state.
"""

import logging
import os
import traceback
from datetime import date, timedelta

import streamlit as st

import ai_client
import quiz_logic
import schedule
import validators

LOGGER = logging.getLogger(__name__)

QUIZ_ERROR = "We couldn't build your quiz right now. Please try again in a moment."
SCHEMA_ERROR = "We couldn't build a usable quiz from those notes. Please try again."
SUBMIT_ERROR = "Please answer all five questions before submitting."
POSITIVE_RESULT = "Great work! No weak topics were identified in this quiz."
SCHEDULE_EMPTY = (
    "There are no study days before your exam date, so there is no revision "
    "plan to show. Choose a later exam date and generate a new quiz."
)
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
        for key in (
            "submitted",
            "score",
            "per_question",
            "weak_topics",
            "schedule",
            "schedule_status",
        ):
            st.session_state.pop(key, None)
        for number in range(1, quiz_logic.QUESTIONS_PER_QUIZ + 1):
            st.session_state.pop(f"answer_{number}", None)


def _on_start_over():
    """Reset the whole workflow to its initial empty state.

    Runs as the button callback, before the page re-runs and before any widget is
    instantiated. Removing the widget-backed keys here (`notes`, `exam_date`,
    `hours`, and `answer_<n>`) is what returns the form to its defaults on the
    next run — a keyed widget falls back to its default once its key is gone. No
    widget key is ever reassigned after its widget exists in the same run.
    """
    keys = [
        "notes",
        "exam_date",
        "hours",
        "errors",
        "ui_error",
        "generate_pending",
        "quiz",
        "submitted",
        "score",
        "per_question",
        "weak_topics",
        "schedule",
        "schedule_status",
    ]
    keys += [
        f"answer_{number}"
        for number in range(1, quiz_logic.QUESTIONS_PER_QUIZ + 1)
    ]
    for key in keys:
        st.session_state.pop(key, None)


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


def _unique_topics(quiz):
    """Return the quiz's topic labels in first-seen order, without repeats.

    This is the full topic list the scheduler falls back to after the weak
    topics, so a clean run still gets a balanced plan.
    """
    topics = []
    seen = set()
    for question in quiz:
        topic = question["topic"]
        if topic not in seen:
            seen.add(topic)
            topics.append(topic)
    return topics


def _build_schedule(quiz, weak_topics, exam_date, hours):
    """Build the revision plan, degrading gracefully if the task call fails.

    Returns (rows, status). Status is "fallback" only when Gemini was asked for
    task text and that call failed; every other path is "done". Python always
    produces a valid plan — the scheduler writes fallback task text when no
    suggestion is available.
    """
    task_suggestions = []
    status = "done"
    if weak_topics:
        try:
            response = ai_client.suggest_tasks(weak_topics)
            task_suggestions = response["tasks"]
        except ai_client.AiError:
            status = "fallback"
    rows = schedule.build_schedule(
        weak_topics,
        _unique_topics(quiz),
        task_suggestions,
        exam_date,
        date.today(),
        hours,
    )
    return rows, status


def _on_submit():
    """Grade the stored answers, or block with a message if any are missing.

    Runs as the button callback, before the page re-runs. Grading and the
    revision plan happen exactly once per click; ordinary reruns only read the
    stored results.
    """
    quiz = st.session_state.get("quiz")
    if not quiz:
        return
    answers = _selected_answers()
    if any(answer is None for answer in answers):
        st.session_state["ui_error"] = SUBMIT_ERROR
        return
    score, per_question = quiz_logic.grade_quiz(quiz, answers)
    weak_topics = quiz_logic.find_weak_topics(quiz, per_question)
    rows, status = _build_schedule(
        quiz,
        weak_topics,
        st.session_state.get("exam_date"),
        st.session_state.get("hours"),
    )
    st.session_state["score"] = score
    st.session_state["per_question"] = per_question
    st.session_state["weak_topics"] = weak_topics
    st.session_state["schedule"] = rows
    st.session_state["schedule_status"] = status
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


def _render_schedule():
    """Show the day-by-day revision plan — the payoff of the whole run.

    Every row comes from `schedule.build_schedule`, so the dates, day numbers,
    and minutes are deterministic. A failed task-suggestion call still leaves a
    complete plan with fallback task text; only a genuinely empty plan (no study
    days before the exam) shows the explanatory message.
    """
    st.subheader("Your revision plan")
    rows = st.session_state.get("schedule") or []
    if not rows:
        st.info(SCHEDULE_EMPTY)
        return
    if st.session_state.get("schedule_status") == "fallback":
        st.caption("Showing suggested tasks. AI task ideas were unavailable.")
    for row in rows:
        with st.container(border=True):
            st.markdown(f"**Day {row['day']} — {row['date']}**")
            st.caption(
                f"{row['topic']} · {row['priority']} · {row['minutes']} minutes"
            )
            st.write(row["task"])


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
        _render_schedule()
    else:
        st.button("Submit Answers", type="primary", key="submit", on_click=_on_submit)
    st.button("Start Over", key="start_over", on_click=_on_start_over)
elif not ui_error:
    st.info(HINT)
