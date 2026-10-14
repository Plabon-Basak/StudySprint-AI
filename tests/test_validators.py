"""Tests for validators.py — the deterministic input rules.

Run with:  .venv\\Scripts\\python -m pytest -q
The dates are fixed so the tests never depend on the real clock.
"""

from datetime import date

import validators

TODAY = date(2026, 1, 1)
TOMORROW = date(2026, 1, 2)
YESTERDAY = date(2025, 12, 31)


# --- notes ------------------------------------------------------------------

def test_empty_notes_are_rejected():
    assert validators.validate_notes("") is not None
    assert validators.validate_notes("   ") is not None
    assert validators.validate_notes(None) is not None


def test_too_short_notes_are_rejected():
    assert validators.validate_notes("a" * 99) is not None


def test_100_char_notes_are_accepted():
    assert validators.validate_notes("a" * 100) is None


def test_notes_are_trimmed_before_counting():
    assert validators.validate_notes("   " + "a" * 100 + "   ") is None
    assert validators.validate_notes("a" * 90 + " " * 20) is not None


# --- exam date --------------------------------------------------------------

def test_exam_date_today_is_rejected():
    assert validators.validate_exam_date(TODAY, TODAY) is not None


def test_exam_date_in_the_past_is_rejected():
    assert validators.validate_exam_date(YESTERDAY, TODAY) is not None


def test_exam_date_tomorrow_is_accepted():
    assert validators.validate_exam_date(TOMORROW, TODAY) is None


# --- daily study hours ------------------------------------------------------

def test_hours_missing_is_rejected():
    assert validators.validate_hours(None) is not None
    assert validators.validate_hours("") is not None


def test_hours_non_numeric_is_rejected():
    assert validators.validate_hours("abc") is not None


def test_hours_below_minimum_is_rejected():
    assert validators.validate_hours(0) is not None
    assert validators.validate_hours(0.49) is not None
    assert validators.validate_hours(-1) is not None


def test_hours_above_maximum_is_rejected():
    assert validators.validate_hours(12.1) is not None
    assert validators.validate_hours(20) is not None


def test_hours_boundaries_are_accepted():
    assert validators.validate_hours(0.5) is None
    assert validators.validate_hours(12) is None
    assert validators.validate_hours(2) is None


def test_hours_nan_is_rejected():
    assert validators.validate_hours(float("nan")) is not None


# --- combined ---------------------------------------------------------------

def test_validate_inputs_reports_each_bad_field():
    errors = validators.validate_inputs("", YESTERDAY, 0, TODAY)
    assert set(errors) == {"notes", "exam_date", "hours"}


def test_validate_inputs_empty_when_all_valid():
    errors = validators.validate_inputs("n" * 120, TOMORROW, 2, TODAY)
    assert errors == {}
