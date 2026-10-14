"""Input validation for StudySprint AI.

Pure Python — no Streamlit, no AI. Every rule from the PRD
(`prd.md > Input form and validation`) lives here as a small function that
takes plain values and returns an error message, or None when the value is
acceptable. Keeping these separate lets us test them on their own.
"""

import math

MIN_NOTES_CHARS = 100
MIN_HOURS = 0.5
MAX_HOURS = 12.0

NOTES_ERROR = (
    "Please paste at least 100 characters of study notes so StudySprint AI "
    "can create a useful quiz."
)
EXAM_DATE_ERROR = (
    "Please choose an exam date at least one day from today so we can build "
    "your revision plan."
)
HOURS_ERROR = "Enter daily study time between 0.5 and 12 hours."


def validate_notes(notes):
    """Return an error message, or None if the notes are usable."""
    text = (notes or "").strip()
    if len(text) < MIN_NOTES_CHARS:
        return NOTES_ERROR
    return None


def validate_exam_date(exam_date, today):
    """Return an error message, or None if the exam date is strictly after today."""
    if exam_date is None or exam_date <= today:
        return EXAM_DATE_ERROR
    return None


def validate_hours(hours):
    """Return an error message, or None if hours are within 0.5-12 inclusive."""
    try:
        value = float(hours)
    except (TypeError, ValueError):
        return HOURS_ERROR
    if math.isnan(value) or value < MIN_HOURS or value > MAX_HOURS:
        return HOURS_ERROR
    return None


def validate_inputs(notes, exam_date, hours, today):
    """Run every check and return a dict of field -> error for the fields that failed.

    An empty dict means all inputs are valid.
    """
    errors = {}

    notes_error = validate_notes(notes)
    if notes_error:
        errors["notes"] = notes_error

    date_error = validate_exam_date(exam_date, today)
    if date_error:
        errors["exam_date"] = date_error

    hours_error = validate_hours(hours)
    if hours_error:
        errors["hours"] = hours_error

    return errors
