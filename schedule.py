"""Deterministic revision-schedule builder for StudySprint AI.

No AI, no Streamlit. Python owns the dates, the day numbers, and the daily
time limit (`prd.md > Revision schedule`). The AI only suggests task text;
anything missing falls back to a plain label.
"""

from datetime import timedelta

FOCUS_MINUTES = 45
REVIEW_MINUTES = 30
MIN_BLOCK_MINUTES = 15


def _task_lookup(task_suggestions):
    """Map topic -> task text from the AI's suggestions (or an empty dict)."""
    lookup = {}
    for item in task_suggestions or []:
        if not isinstance(item, dict):
            continue
        topic = item.get("topic")
        task = item.get("task")
        if isinstance(topic, str) and isinstance(task, str):
            topic = topic.strip()
            task = task.strip()
            if topic and task:
                lookup[topic] = task
    return lookup


def _ordered_topics(weak_topics, all_topics):
    """Weak topics first (in the order given), then the remaining topics.

    Returns (ordered_topic_names, set_of_weak_names).
    """
    ordered = []
    seen = set()
    weak_names = []
    for item in weak_topics or []:
        topic = item.get("topic") if isinstance(item, dict) else None
        if isinstance(topic, str) and topic:
            if topic not in seen:
                seen.add(topic)
                ordered.append(topic)
            if topic not in weak_names:
                weak_names.append(topic)
    for topic in all_topics or []:
        if isinstance(topic, str) and topic and topic not in seen:
            seen.add(topic)
            ordered.append(topic)
    return ordered, set(weak_names)


def build_schedule(weak_topics, all_topics, task_suggestions, exam_date, today, daily_hours):
    """Return the day-by-day revision plan as a list of row dicts.

    Each row is {day, date, topic, priority, task, minutes}. The plan starts on
    `today` (day 1) and stops the day before `exam_date`, so nothing is ever
    scheduled on or after the exam. A day's total minutes never exceeds
    `daily_hours`. Returns [] when there is no study day before the exam.
    """
    if exam_date is None or today is None or exam_date <= today:
        return []

    ordered, weak_set = _ordered_topics(weak_topics, all_topics)
    if not ordered:
        return []

    tasks = _task_lookup(task_suggestions)
    daily_minutes = int(round(daily_hours * 60))
    num_days = (exam_date - today).days

    schedule = []
    pointer = 0
    for day_index in range(num_days):
        day_date = today + timedelta(days=day_index)
        remaining = daily_minutes
        blocks_today = 0
        while remaining >= MIN_BLOCK_MINUTES and blocks_today < len(ordered):
            topic = ordered[pointer % len(ordered)]
            pointer += 1
            blocks_today += 1

            priority = "weak" if topic in weak_set else "review"
            block = FOCUS_MINUTES if priority == "weak" else REVIEW_MINUTES
            minutes = min(block, remaining)
            if minutes < MIN_BLOCK_MINUTES:
                break

            task = tasks.get(topic)
            if not task:
                task = (
                    f"Focused revision: {topic}"
                    if priority == "weak"
                    else f"Light review: {topic}"
                )

            schedule.append(
                {
                    "day": day_index + 1,
                    "date": day_date.isoformat(),
                    "topic": topic,
                    "priority": priority,
                    "task": task,
                    "minutes": minutes,
                }
            )
            remaining -= minutes
    return schedule
