"""Integration tests for app.py using Streamlit's AppTest.

The AI client is mocked, so these tests never touch the network and need no API
key. They drive the real app script: fill the form, click Generate, and inspect
the rendered page and session state.
"""

import logging
from datetime import date, timedelta
from pathlib import Path
from unittest.mock import patch

import pytest
from streamlit.testing.v1 import AppTest, AppTestError

import ai_client

APP_PATH = str(Path(__file__).resolve().parents[1] / "app.py")
NOTES = "Cell respiration releases energy from glucose. " * 4


def _valid_quiz():
    return {
        "questions": [
            {
                "question": f"Question number {i}",
                "topic": f"Topic label {i}",
                "options": [f"Opt {i}A", f"Opt {i}B", f"Opt {i}C", f"Opt {i}D"],
                "correct_index": 0,
                "explanation": f"Explanation marker {i}",
            }
            for i in range(1, 6)
        ]
    }


def _new_app():
    at = AppTest.from_file(APP_PATH)
    at.run()
    return at


def _fill_valid_inputs(at):
    at.text_area(key="notes").set_value(NOTES)
    at.number_input(key="hours").set_value(2.0)
    at.date_input(key="exam_date").set_value(date.today() + timedelta(days=7))
    return at


def _answer_all(at, letter="A"):
    """Select the option ending in `letter` for all five questions."""
    for number in range(1, 6):
        at.radio(key=f"answer_{number}").set_value(f"Opt {number}{letter}")
    return at


def _answer_weak(at):
    """Answer question 1 correctly and 2-5 wrongly, producing weak topics."""
    at.radio(key="answer_1").set_value("Opt 1A")
    for number in range(2, 6):
        at.radio(key=f"answer_{number}").set_value(f"Opt {number}B")
    return at.run()


def _tasks_for(weak_topics):
    """A fake `suggest_tasks` response that names each weak topic's task."""
    return {
        "tasks": [
            {"topic": item["topic"], "task": f"Revise {item['topic']}"}
            for item in weak_topics
        ]
    }


def _generate(at, quiz=None):
    """Fill the form and generate a quiz, with the AI mocked."""
    with patch.object(ai_client, "generate_quiz", return_value=quiz or _valid_quiz()):
        _fill_valid_inputs(at)
        at.button(key="generate").click().run()
    return at


def _rendered_text(at):
    parts = [element.value for element in at.markdown]
    parts += [element.value for element in at.caption]
    return " ".join(parts)


def test_valid_inputs_render_five_questions(monkeypatch):
    with patch.object(ai_client, "generate_quiz", return_value=_valid_quiz()) as generate:
        at = _new_app()
        _fill_valid_inputs(at)
        at.button(key="generate").click().run()

    assert generate.call_count == 1
    assert generate.call_args.args[0] == NOTES

    assert len(at.session_state.get("quiz")) == 5
    assert len(at.radio) == 5
    for radio in at.radio:
        assert len(radio.options) == 4

    text = _rendered_text(at)
    assert "Question number 1" in text
    assert "Topic label 1" in text


def test_answers_and_explanations_are_hidden(monkeypatch):
    with patch.object(ai_client, "generate_quiz", return_value=_valid_quiz()):
        at = _new_app()
        _fill_valid_inputs(at)
        at.button(key="generate").click().run()

    text = _rendered_text(at)
    assert "Explanation marker" not in text


def test_invalid_inputs_make_no_ai_call():
    with patch.object(ai_client, "generate_quiz") as generate:
        at = _new_app()
        at.button(key="generate").click().run()

    assert generate.call_count == 0
    assert len(at.error) >= 1
    assert at.session_state.get("quiz") is None


def test_api_error_shows_retry_and_keeps_inputs():
    with patch.object(ai_client, "generate_quiz", side_effect=ai_client.AiError("down")):
        at = _new_app()
        _fill_valid_inputs(at)
        at.button(key="generate").click().run()

    assert at.session_state.get("quiz") is None
    assert any("try again" in error.value.lower() for error in at.error)
    assert at.text_area(key="notes").value == NOTES


def test_invalid_quiz_shows_retry():
    invalid = {"questions": _valid_quiz()["questions"][:4]}
    with patch.object(ai_client, "generate_quiz", return_value=invalid):
        at = _new_app()
        _fill_valid_inputs(at)
        at.button(key="generate").click().run()

    assert at.session_state.get("quiz") is None
    assert any("try again" in error.value.lower() for error in at.error)


def test_reruns_do_not_call_the_ai_again(monkeypatch):
    with patch.object(ai_client, "generate_quiz", return_value=_valid_quiz()) as generate:
        at = _new_app()
        _fill_valid_inputs(at)
        at.button(key="generate").click().run()
        assert generate.call_count == 1

        at.run()
        assert generate.call_count == 1

        at.radio(key="answer_1").set_value("Opt 1B").run()
        assert generate.call_count == 1


def test_quiz_is_stored_but_not_answers():
    with patch.object(ai_client, "generate_quiz", return_value=_valid_quiz()):
        at = _new_app()
        _fill_valid_inputs(at)
        at.button(key="generate").click().run()

    quiz = at.session_state.get("quiz")
    assert quiz is not None
    assert "correct_index" in quiz[0]
    assert at.session_state.get("submitted") is None


def test_submit_all_correct_scores_five():
    at = _generate(_new_app())
    _answer_all(at).run()
    at.button(key="submit").click().run()

    assert at.session_state.get("submitted") is True
    assert at.session_state.get("score") == 5
    assert at.session_state.get("weak_topics") == []
    assert "Score: 5 / 5" in _rendered_text(at)


def test_submit_with_unanswered_question_is_blocked():
    at = _generate(_new_app())
    at.radio(key="answer_1").set_value("Opt 1A").run()
    at.button(key="submit").click().run()

    assert not at.session_state.get("submitted")
    assert at.session_state.get("score") is None
    assert any("answer all five" in error.value.lower() for error in at.error)
    assert len(at.radio) == 5


def test_correct_answers_and_explanations_hidden_until_submit():
    at = _generate(_new_app())
    assert "Explanation marker" not in _rendered_text(at)
    assert "Correct answer:" not in _rendered_text(at)

    _answer_all(at).run()
    at.button(key="submit").click().run()

    text = _rendered_text(at)
    assert "Correct answer: Opt 1A" in text
    assert "Explanation marker 1" in text


def test_wrong_answers_show_correct_answer_and_weak_topics():
    at = _generate(_new_app())
    at.radio(key="answer_1").set_value("Opt 1A")
    for number in range(2, 6):
        at.radio(key=f"answer_{number}").set_value(f"Opt {number}B")
    at.run()
    at.button(key="submit").click().run()

    assert at.session_state.get("score") == 1
    weak = at.session_state.get("weak_topics")
    assert [item["topic"] for item in weak] == [
        "Topic label 2",
        "Topic label 3",
        "Topic label 4",
        "Topic label 5",
    ]
    text = _rendered_text(at)
    assert "Score: 1 / 5" in text
    assert "Your answer: Opt 2B" in text
    assert "Correct answer: Opt 2A" in text
    assert "Explanation marker 2" in text


def test_all_correct_shows_positive_message():
    at = _generate(_new_app())
    _answer_all(at).run()
    at.button(key="submit").click().run()

    assert at.session_state.get("weak_topics") == []
    assert any("No weak topics" in message.value for message in at.success)


def test_answers_lock_after_submit():
    at = _generate(_new_app())
    _answer_all(at).run()
    at.button(key="submit").click().run()

    assert all(radio.disabled for radio in at.radio)
    with pytest.raises(AppTestError):
        at.radio(key="answer_1").set_value("Opt 1B")


def test_rerun_preserves_results_without_new_ai_call():
    with patch.object(ai_client, "generate_quiz", return_value=_valid_quiz()) as generate:
        at = _new_app()
        _fill_valid_inputs(at)
        at.button(key="generate").click().run()
        _answer_all(at).run()
        at.button(key="submit").click().run()
        assert generate.call_count == 1

        at.run()
        assert generate.call_count == 1

    assert at.session_state.get("score") == 5
    assert "Score: 5 / 5" in _rendered_text(at)


def test_regenerate_clears_previous_results_and_answers():
    with patch.object(ai_client, "generate_quiz", return_value=_valid_quiz()) as generate:
        at = _new_app()
        _fill_valid_inputs(at)
        at.button(key="generate").click().run()
        _answer_all(at).run()
        at.button(key="submit").click().run()
        assert at.session_state.get("submitted") is True

        _fill_valid_inputs(at)
        at.button(key="generate").click().run()

    assert generate.call_count == 2
    assert not at.session_state.get("submitted")
    assert at.session_state.get("score") is None
    assert at.session_state.get("answer_1") is None
    assert at.session_state.get("weak_topics") is None
    assert "Score:" not in _rendered_text(at)


def test_api_failure_logs_real_error_but_shows_generic_message(monkeypatch, caplog):
    """The terminal must show the real exception; the browser must not leak secrets."""
    monkeypatch.setenv("GEMINI_API_KEY", "secret-key-12345")
    failure = ai_client.AiError(
        "The AI request failed: 429 RESOURCE_EXHAUSTED (attempt with key secret-key-12345)"
    )
    with patch.object(ai_client, "generate_quiz", side_effect=failure):
        at = _new_app()
        _fill_valid_inputs(at)
        with caplog.at_level(logging.ERROR):
            at.button(key="generate").click().run()

    errors = [error.value for error in at.error]
    assert any("try again" in value.lower() for value in errors)
    assert all("429" not in value for value in errors)

    assert "AiError" in caplog.text
    assert "429 RESOURCE_EXHAUSTED" in caplog.text
    assert "secret-key-12345" not in caplog.text
    assert "[redacted]" in caplog.text
    assert all("secret-key-12345" not in value for value in errors)


def test_schema_rejection_logs_reason_but_shows_generic_message(caplog):
    """A schema rejection logs why it failed while the UI stays generic."""
    invalid = {"questions": _valid_quiz()["questions"][:4]}
    with patch.object(ai_client, "generate_quiz", return_value=invalid):
        at = _new_app()
        _fill_valid_inputs(at)
        with caplog.at_level(logging.ERROR):
            at.button(key="generate").click().run()

    errors = [error.value for error in at.error]
    assert any("try again" in value.lower() for value in errors)
    assert at.session_state.get("quiz") is None
    assert "exactly 5 questions" in caplog.text


def _submitted_schedule(at):
    return at.session_state.get("schedule")


def test_weak_submission_calls_suggest_tasks_once_and_renders_schedule():
    at = _generate(_new_app())
    _answer_weak(at)

    with patch.object(ai_client, "suggest_tasks", side_effect=_tasks_for) as suggest:
        at.button(key="submit").click().run()

    weak = at.session_state.get("weak_topics")
    assert weak  # questions 2-5 were wrong
    assert suggest.call_count == 1
    assert suggest.call_args.args[0] == weak

    rows = _submitted_schedule(at)
    assert rows
    assert at.session_state.get("schedule_status") == "done"

    text = _rendered_text(at)
    assert "Your revision plan" in " ".join(s.value for s in at.subheader)
    assert "Day 1" in text
    assert "Revise Topic label 2" in text
    assert "minutes" in text


def test_schedule_starts_today_and_ends_before_exam():
    at = _generate(_new_app())
    exam_date = at.session_state.get("exam_date")
    _answer_weak(at)

    with patch.object(ai_client, "suggest_tasks", return_value={"tasks": []}):
        at.button(key="submit").click().run()

    rows = _submitted_schedule(at)
    dates = sorted({row["date"] for row in rows})
    assert dates[0] == date.today().isoformat()
    assert all(row["date"] < exam_date.isoformat() for row in rows)


def test_schedule_respects_the_daily_budget():
    at = _generate(_new_app())
    _answer_weak(at)

    with patch.object(ai_client, "suggest_tasks", return_value={"tasks": []}):
        at.button(key="submit").click().run()

    rows = _submitted_schedule(at)
    limit = int(round(at.session_state.get("hours") * 60))
    minutes_per_day = {}
    for row in rows:
        minutes_per_day[row["day"]] = minutes_per_day.get(row["day"], 0) + row["minutes"]
    assert minutes_per_day
    assert all(total <= limit for total in minutes_per_day.values())


def test_all_correct_skips_suggest_tasks_and_builds_review_plan():
    at = _generate(_new_app())
    _answer_all(at).run()

    with patch.object(ai_client, "suggest_tasks", return_value={"tasks": []}) as suggest:
        at.button(key="submit").click().run()

    assert suggest.call_count == 0
    assert at.session_state.get("schedule_status") == "done"

    rows = _submitted_schedule(at)
    assert rows
    assert all(row["priority"] == "review" for row in rows)


def test_task_call_failure_keeps_submission_and_uses_fallback():
    at = _generate(_new_app())
    _answer_weak(at)

    with patch.object(ai_client, "suggest_tasks", side_effect=ai_client.AiError("quota")):
        at.button(key="submit").click().run()

    assert at.session_state.get("submitted") is True
    assert at.session_state.get("schedule_status") == "fallback"

    rows = _submitted_schedule(at)
    assert rows
    text = _rendered_text(at)
    assert "Focused revision: Topic label 2" in text
    assert "quota" not in text


def test_regenerate_clears_previous_schedule():
    at = _generate(_new_app())
    _answer_weak(at)
    with patch.object(ai_client, "suggest_tasks", return_value={"tasks": []}):
        at.button(key="submit").click().run()
    assert _submitted_schedule(at)

    with patch.object(ai_client, "generate_quiz", return_value=_valid_quiz()):
        _fill_valid_inputs(at)
        at.button(key="generate").click().run()

    assert at.session_state.get("schedule") is None
    assert at.session_state.get("schedule_status") is None
    assert "Your revision plan" not in " ".join(s.value for s in at.subheader)


def _submit_all_correct(at):
    """Generate is assumed done; answer everything and submit (AI mocked)."""
    _answer_all(at).run()
    with patch.object(ai_client, "suggest_tasks", return_value={"tasks": []}):
        at.button(key="submit").click().run()
    return at


def test_start_over_resets_workflow_state():
    at = _generate(_new_app())
    _submit_all_correct(at)
    assert at.session_state.get("submitted") is True
    assert at.session_state.get("schedule")

    at.button(key="start_over").click().run()

    for key in (
        "quiz",
        "submitted",
        "score",
        "per_question",
        "weak_topics",
        "schedule",
        "schedule_status",
        "ui_error",
        "errors",
        "generate_pending",
    ):
        assert at.session_state.get(key) is None, key
    for number in range(1, 6):
        assert at.session_state.get(f"answer_{number}") is None, number

    # Widget-backed inputs are back to their defaults.
    assert at.session_state.get("notes") == ""
    assert at.session_state.get("exam_date") == date.today() + timedelta(days=1)
    assert at.session_state.get("hours") == 2.0


def test_start_over_returns_to_initial_ui():
    at = _generate(_new_app())
    _submit_all_correct(at)
    assert "Score:" in _rendered_text(at)

    at.button(key="start_over").click().run()

    assert len(at.radio) == 0
    assert len(at.error) == 0
    assert "Score:" not in _rendered_text(at)

    subheaders = " ".join(s.value for s in at.subheader)
    assert "Your quiz" not in subheaders
    assert "Your results" not in subheaders
    assert "Your revision plan" not in subheaders

    assert any("after you generate your quiz" in info.value for info in at.info)
    assert not any(button.key == "start_over" for button in at.button)


def test_can_generate_a_fresh_quiz_after_start_over():
    at = _generate(_new_app())
    _submit_all_correct(at)
    at.button(key="start_over").click().run()

    with patch.object(ai_client, "generate_quiz", return_value=_valid_quiz()) as generate:
        _fill_valid_inputs(at)
        at.button(key="generate").click().run()

    assert generate.call_count == 1
    assert len(at.radio) == 5
    assert at.session_state.get("submitted") is None
    assert "Question number 1" in _rendered_text(at)
    assert any(button.key == "start_over" for button in at.button)
