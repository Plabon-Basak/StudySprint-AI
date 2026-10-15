"""Tests for ai_client. The Gemini SDK is monkeypatched — no real API calls."""

import json
import os

import pytest

import ai_client


class FakeResponse:
    def __init__(self, text=None, parsed=None):
        self.text = text
        self.parsed = parsed


class FakeModels:
    def __init__(self, outcome):
        self.outcome = outcome
        self.calls = []

    def generate_content(self, model=None, contents=None, config=None):
        self.calls.append({"model": model, "contents": contents, "config": config})
        if isinstance(self.outcome, Exception):
            raise self.outcome
        return self.outcome


class FakeClient:
    def __init__(self, outcome):
        self.models = FakeModels(outcome)


def install(monkeypatch, outcome, key="test-key"):
    """Replace the Gemini SDK client and env with deterministic fakes."""
    fake = FakeClient(outcome)
    fake.client_calls = []
    monkeypatch.setattr(ai_client, "load_dotenv", lambda: None)
    if key is None:
        monkeypatch.delenv("GEMINI_API_KEY", raising=False)
        monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    else:
        monkeypatch.setenv("GEMINI_API_KEY", key)

    def fake_client(*, api_key=None, http_options=None):
        fake.client_calls.append({"api_key": api_key, "http_options": http_options})
        return fake

    monkeypatch.setattr(ai_client.genai, "Client", fake_client)
    return fake


def _quiz_dict(count=5):
    return {
        "questions": [
            {
                "question": f"Question {i}",
                "topic": f"Topic {i}",
                "options": ["a", "b", "c", "d"],
                "correct_index": 0,
                "explanation": "Because.",
            }
            for i in range(count)
        ]
    }


def test_generate_quiz_parses_json(monkeypatch):
    fake = install(monkeypatch, FakeResponse(text=json.dumps(_quiz_dict())))
    result = ai_client.generate_quiz("some notes")
    assert len(result["questions"]) == 5
    assert fake.models.calls[0]["model"] == ai_client.DEFAULT_MODEL


def test_generate_quiz_prefers_parsed_output(monkeypatch):
    install(monkeypatch, FakeResponse(parsed=_quiz_dict()))
    assert len(ai_client.generate_quiz("notes")["questions"]) == 5


def test_model_name_is_configurable(monkeypatch):
    monkeypatch.setenv("GEMINI_MODEL", "gemini-2.5-flash")
    fake = install(monkeypatch, FakeResponse(text=json.dumps(_quiz_dict())))
    ai_client.generate_quiz("notes")
    assert fake.models.calls[0]["model"] == "gemini-2.5-flash"


def test_model_name_loads_dotenv_before_reading(monkeypatch):
    """A GEMINI_MODEL that only lives in `.env` must be loaded before it is read."""
    monkeypatch.delenv("GEMINI_MODEL", raising=False)

    def fake_load_dotenv():
        os.environ["GEMINI_MODEL"] = "gemini-from-dotenv"

    monkeypatch.setattr(ai_client, "load_dotenv", fake_load_dotenv)
    assert ai_client._model_name() == "gemini-from-dotenv"


def test_model_name_does_not_override_existing_env(monkeypatch):
    """An environment variable set by the OS keeps priority over `.env`."""
    monkeypatch.setenv("GEMINI_MODEL", "os-provided-model")

    def fake_load_dotenv():
        os.environ.setdefault("GEMINI_MODEL", "gemini-from-dotenv")

    monkeypatch.setattr(ai_client, "load_dotenv", fake_load_dotenv)
    assert ai_client._model_name() == "os-provided-model"


def test_config_requests_structured_json(monkeypatch):
    fake = install(monkeypatch, FakeResponse(text=json.dumps(_quiz_dict())))
    ai_client.generate_quiz("notes")
    config = fake.models.calls[0]["config"]
    assert config.response_mime_type == "application/json"
    assert config.response_schema == ai_client.QUIZ_RESPONSE_SCHEMA
    assert config.temperature == ai_client.TEMPERATURE


def test_client_uses_bounded_retries(monkeypatch):
    fake = install(monkeypatch, FakeResponse(text=json.dumps(_quiz_dict())))
    ai_client.generate_quiz("notes")
    http_options = fake.client_calls[0]["http_options"]
    assert http_options is not None
    assert http_options.retry_options is not None
    assert http_options.retry_options.attempts == ai_client.RETRY_ATTEMPTS == 4


def test_malformed_json_raises(monkeypatch):
    install(monkeypatch, FakeResponse(text="{not valid json"))
    with pytest.raises(ai_client.AiError):
        ai_client.generate_quiz("notes")


def test_non_object_json_raises(monkeypatch):
    install(monkeypatch, FakeResponse(text=json.dumps(["a", "b"])))
    with pytest.raises(ai_client.AiError):
        ai_client.generate_quiz("notes")


def test_invalid_quiz_shape_raises(monkeypatch):
    install(monkeypatch, FakeResponse(text=json.dumps({"questions": "oops"})))
    with pytest.raises(ai_client.AiError):
        ai_client.generate_quiz("notes")


def test_empty_response_raises(monkeypatch):
    install(monkeypatch, FakeResponse(text=""))
    with pytest.raises(ai_client.AiError):
        ai_client.generate_quiz("notes")


def test_api_error_raises(monkeypatch):
    install(monkeypatch, RuntimeError("service unavailable"))
    with pytest.raises(ai_client.AiError):
        ai_client.generate_quiz("notes")


def test_rate_limit_error_raises(monkeypatch):
    install(monkeypatch, RuntimeError("429 RESOURCE_EXHAUSTED"))
    with pytest.raises(ai_client.AiError):
        ai_client.generate_quiz("notes")


def test_missing_key_raises(monkeypatch):
    install(monkeypatch, FakeResponse(text=json.dumps(_quiz_dict())), key=None)
    with pytest.raises(ai_client.AiError):
        ai_client.generate_quiz("notes")


def test_suggest_tasks_accepts_dicts_and_strings(monkeypatch):
    tasks = {"tasks": [{"topic": "Fractions", "task": "Redo 5 fraction sums"}]}
    install(monkeypatch, FakeResponse(text=json.dumps(tasks)))
    result = ai_client.suggest_tasks([{"topic": "Fractions", "mistakes": 2}, "Algebra"])
    assert result["tasks"][0]["topic"] == "Fractions"


def test_suggest_tasks_prompt_lists_topics(monkeypatch):
    fake = install(monkeypatch, FakeResponse(text=json.dumps({"tasks": []})))
    ai_client.suggest_tasks([{"topic": "Fractions", "mistakes": 1}])
    assert "Fractions" in fake.models.calls[0]["contents"]


def test_suggest_tasks_invalid_shape_raises(monkeypatch):
    install(monkeypatch, FakeResponse(text=json.dumps({"nope": []})))
    with pytest.raises(ai_client.AiError):
        ai_client.suggest_tasks(["Fractions"])
