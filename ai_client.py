"""Gemini integration for StudySprint AI.

This is the only module that talks to the internet. It sends the student's
notes (or the weak-topic names) to the Gemini API and returns the response as a
plain Python dictionary. It does no grading and no date or schedule logic — those
belong to `quiz_logic.py` and `schedule.py`.
"""

import json
import os

from dotenv import load_dotenv
from google import genai
from google.genai import types

DEFAULT_MODEL = "gemini-flash-latest"
TEMPERATURE = 0.4
RETRY_ATTEMPTS = 4

QUIZ_RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "questions": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "question": {"type": "string"},
                    "topic": {"type": "string"},
                    "options": {"type": "array", "items": {"type": "string"}},
                    "correct_index": {"type": "integer"},
                    "explanation": {"type": "string"},
                },
                "required": [
                    "question",
                    "topic",
                    "options",
                    "correct_index",
                    "explanation",
                ],
            },
        }
    },
    "required": ["questions"],
}

TASKS_RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "tasks": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "topic": {"type": "string"},
                    "task": {"type": "string"},
                },
                "required": ["topic", "task"],
            },
        }
    },
    "required": ["tasks"],
}


class AiError(Exception):
    """Raised when the Gemini call fails or returns unusable output."""


def _model_name():
    """Return the configured model, loading `.env` first so it is never read stale.

    `load_dotenv()` keeps its default (no override), so a `GEMINI_MODEL` set by
    the operating system still wins over the value in `.env`.
    """
    load_dotenv()
    return os.environ.get("GEMINI_MODEL", DEFAULT_MODEL)


def _make_client():
    load_dotenv()
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise AiError(
            "No Gemini API key found. Add GEMINI_API_KEY to your .env file."
        )
    return genai.Client(
        api_key=api_key,
        http_options=types.HttpOptions(
            retry_options=types.HttpRetryOptions(attempts=RETRY_ATTEMPTS)
        ),
    )


def _generate(schema, prompt, list_key):
    """Call Gemini, parse the JSON, and return the response as a dictionary.

    `list_key` is the key the answer list must live under ("questions" or
    "tasks"). Anything else — an API failure, a rate limit, malformed JSON, or
    an unexpected shape — is raised as a single `AiError`.
    """
    client = _make_client()
    try:
        response = client.models.generate_content(
            model=_model_name(),
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=schema,
                temperature=TEMPERATURE,
            ),
        )
    except AiError:
        raise
    except Exception as exc:
        raise AiError(f"The AI request failed: {exc}") from exc

    data = getattr(response, "parsed", None)
    if data is None:
        text = getattr(response, "text", None)
        if not text:
            raise AiError("The AI returned an empty response.")
        try:
            data = json.loads(text)
        except (json.JSONDecodeError, TypeError) as exc:
            raise AiError("The AI returned invalid JSON.") from exc

    if not isinstance(data, dict) or not isinstance(data.get(list_key), list):
        raise AiError("The AI returned an unexpected response shape.")
    return data


def generate_quiz(notes):
    """Ask Gemini for exactly five multiple-choice questions from `notes`."""
    prompt = (
        "You are a study coach helping a student revise. Read the study notes "
        "below and write exactly five multiple-choice questions that test the "
        "most important ideas. Each question needs four answer options with "
        "exactly one correct answer, a short topic label of a few words, and a "
        "one-sentence explanation of why the correct answer is right. Keep the "
        "questions clear and answerable from the notes alone.\n\n"
        f"Study notes:\n{notes}"
    )
    return _generate(QUIZ_RESPONSE_SCHEMA, prompt, "questions")


def suggest_tasks(topics):
    """Ask Gemini for one short revision task per weak topic."""
    names = _topic_names(topics)
    listing = "\n".join(f"- {name}" for name in names)
    prompt = (
        "You are a study coach. The student answered questions on the topics "
        "below incorrectly. For each topic, suggest one short, concrete "
        "revision task in a single sentence.\n\n"
        f"Topics:\n{listing}"
    )
    return _generate(TASKS_RESPONSE_SCHEMA, prompt, "tasks")


def _topic_names(topics):
    """Accept topic names as strings or as {'topic': ...} dicts."""
    names = []
    for item in topics or []:
        name = item.get("topic") if isinstance(item, dict) else item
        if isinstance(name, str) and name.strip():
            names.append(name.strip())
    return names
