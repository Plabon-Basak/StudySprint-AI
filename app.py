"""StudySprint AI — single-page Streamlit app.

Slice 1: the input form, the empty-state hint, and inline validation for the
three inputs. There is no AI yet — clicking Generate Quiz only checks the
inputs and shows messages for anything that fails.
"""

from datetime import date, timedelta

import streamlit as st

import validators

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
    """Validate the current inputs and store the messages. Runs before the rerun."""
    st.session_state["errors"] = validators.validate_inputs(
        st.session_state.get("notes", ""),
        st.session_state.get("exam_date"),
        st.session_state.get("hours"),
        date.today(),
    )


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

    st.button("Generate Quiz", type="primary", on_click=_on_generate)

st.info(
    "Your personalized quiz, results, and revision plan will appear here "
    "after you generate your quiz."
)
