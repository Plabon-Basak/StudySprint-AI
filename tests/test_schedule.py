"""Tests for schedule.build_schedule: dates, day numbers, and the time limit."""

from datetime import date, timedelta

import schedule

TODAY = date(2026, 1, 1)
TOMORROW = date(2026, 1, 2)
IN_THREE_DAYS = date(2026, 1, 4)


def _minutes_on(rows, day):
    return sum(row["minutes"] for row in rows if row["day"] == day)


def test_no_study_day_returns_empty():
    assert schedule.build_schedule([], ["A"], None, TODAY, TODAY, 2) == []


def test_exam_in_the_past_returns_empty():
    assert schedule.build_schedule([], ["A"], None, date(2025, 1, 1), TODAY, 2) == []


def test_single_study_day_still_produces_a_plan():
    rows = schedule.build_schedule([], ["A", "B"], None, TOMORROW, TODAY, 2)
    assert rows != []
    assert all(row["day"] == 1 for row in rows)
    assert rows[0]["date"] == TODAY.isoformat()


def test_schedule_spans_today_to_day_before_exam():
    rows = schedule.build_schedule([], ["A", "B", "C"], None, IN_THREE_DAYS, TODAY, 2)
    dates = sorted({row["date"] for row in rows})
    assert dates[0] == TODAY.isoformat()
    assert dates[-1] == (IN_THREE_DAYS - timedelta(days=1)).isoformat()


def test_no_task_on_or_after_exam_date():
    rows = schedule.build_schedule([], ["A", "B", "C", "D"], None, IN_THREE_DAYS, TODAY, 3)
    exam = IN_THREE_DAYS.isoformat()
    assert all(row["date"] < exam for row in rows)


def test_day_numbers_are_sequential():
    rows = schedule.build_schedule([], ["A"], None, IN_THREE_DAYS, TODAY, 2)
    assert sorted({row["day"] for row in rows}) == [1, 2, 3]


def test_daily_minutes_never_exceed_limit():
    weak = [{"topic": "A", "mistakes": 2}, {"topic": "B", "mistakes": 1}]
    topics = ["A", "B", "C", "D", "E"]
    for hours in (0.5, 1, 1.5, 2, 3.5, 12):
        rows = schedule.build_schedule(weak, topics, None, IN_THREE_DAYS, TODAY, hours)
        limit = int(round(hours * 60))
        for day in {row["day"] for row in rows}:
            assert _minutes_on(rows, day) <= limit


def test_every_day_has_at_least_one_task():
    rows = schedule.build_schedule([], ["A", "B"], None, IN_THREE_DAYS, TODAY, 2)
    assert sorted({row["day"] for row in rows}) == [1, 2, 3]


def test_weak_topics_appear_before_review_topics():
    rows = schedule.build_schedule(
        [{"topic": "A", "mistakes": 3}, {"topic": "B", "mistakes": 1}],
        ["A", "B", "C", "D", "E"],
        None,
        TOMORROW,
        TODAY,
        1.5,
    )
    assert [row["priority"] for row in rows][:2] == ["weak", "weak"]
    assert rows[0]["topic"] == "A"


def test_all_correct_gives_balanced_review_plan():
    rows = schedule.build_schedule([], ["A", "B", "C"], None, IN_THREE_DAYS, TODAY, 2)
    assert rows != []
    assert all(row["priority"] == "review" for row in rows)


def test_uses_ai_task_text_and_falls_back():
    rows = schedule.build_schedule(
        [{"topic": "A", "mistakes": 1}],
        ["A", "B"],
        [{"topic": "A", "task": "Redo the A practice set"}],
        TOMORROW,
        TODAY,
        2,
    )
    first_by_topic = {}
    for row in rows:
        first_by_topic.setdefault(row["topic"], row)
    assert first_by_topic["A"]["task"] == "Redo the A practice set"
    assert first_by_topic["B"]["task"] == "Light review: B"


def test_minutes_are_positive_integers():
    rows = schedule.build_schedule([], ["A", "B"], None, IN_THREE_DAYS, TODAY, 1.25)
    for row in rows:
        assert isinstance(row["minutes"], int)
        assert row["minutes"] > 0
