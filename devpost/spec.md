---
doc: spec
status: approved
---

# StudySprint AI — Technical Spec

## How This Works, In Plain Language

StudySprint AI is one Streamlit page backed by a few small Python files. It has three kinds of pieces:

1. **The page** (`app.py`). Streamlit is a Python library that turns a script into a web page. Every time you click something, the script re-runs top to bottom. To stop the quiz from disappearing on each click, we keep the important pieces in `st.session_state` — a small memory Streamlit keeps for the current visitor, which is cleared when the app restarts.

2. **The AI helper** (`ai_client.py`). This is the only file that talks to the internet. It sends your notes to Google's Gemini API and asks for five questions plus short revision tasks, in a fixed JSON shape. It must be configurable (which model, which key) and it never grades anything.

3. **The deterministic brain** (`validators.py`, `quiz_logic.py`, `schedule.py`). These are plain Python functions with no AI and no internet. They decide whether inputs are valid, check the AI's JSON, grade the quiz, group weak topics, and build the day-by-day schedule. Because they're pure Python, we can test them exactly and the results are always the same for the same input.

Why this shape: the part that can be unpredictable (the AI) is boxed into one file, and the part that must be trustworthy (grading and the schedule) is plain Python we can test. That matches the PRD's rule that grading, dates, topic grouping, and the daily time limit stay deterministic in Python (`prd.md > Product Decisions`).

## The Core Journey Through the System

PRD ref: `prd.md > The Core Journey`.

1. **Student opens the app.** `app.py` draws the title, description, the empty input form, and the empty-state hint. Nothing is stored yet.
2. **They paste notes, pick an exam date, set daily hours.** Streamlit's widgets hold these values in the widget keys.
3. **They click Generate Quiz.** `app.py` calls `validators.validate_inputs(...)`. If invalid, it shows the inline messages and stops — `ai_client` is never called (`prd.md > Input form and validation`).
4. **Inputs valid → the AI runs.** `ai_client.generate_quiz(notes)` calls Gemini and returns a raw dictionary. `quiz_logic.validate_quiz(raw)` checks it against the schema. If it passes, the quiz is stored in `st.session_state["quiz"]`; if not, an error + retry is shown and nothing is stored (`prd.md > Quiz generation`).
5. **Five questions render below the form.** Each question shows its topic label and four radio options. Selecting a radio only updates stored answers — no new AI call (`prd.md > Answering and submission`).
6. **They click Submit Answers.** If any question is unanswered, a message blocks it. Otherwise `quiz_logic.grade_quiz(...)` scores the run and `quiz_logic.find_weak_topics(...)` groups mistakes by topic.
7. **The schedule is built.** If there are weak topics, `ai_client.suggest_tasks(weak_topics)` returns a short task per topic; if every answer is correct, that call is skipped and a balanced plan is built without inventing weak topics. Either way, `schedule.build_schedule(...)` turns tasks into dated rows, sets day numbers and minutes, prioritizes weak topics first, and enforces the daily limit in Python (`prd.md > Revision schedule`).
8. **Results + schedule render.** Score, per-question feedback, weak-topic summary, and the day-by-day plan come from `st.session_state`, so reruns don't recompute them.
9. **Start Over** clears the quiz-related state and returns to step 1.

## Stack

- **Language:** Python 3.10+.
- **UI:** Streamlit — single-page app from one script; supports the session state and simple cards the PRD asks for. Docs: https://docs.streamlit.io
- **AI SDK:** `google-genai` (official Google Gen AI Python SDK) — structured JSON output via `response_schema`, and a configurable model name. Docs: https://googleapis.github.io/python-genai/ · https://github.com/googleapis/python-genai · Structured output: https://ai.google.dev/gemini-api/docs/structured-output
- **Config:** `python-dotenv` to load a local `.env` file (so the API key stays out of the code and out of Git).
- **Tests:** `pytest`. Docs: https://docs.pytest.org
- **Model:** chosen as a current Gemini Flash model via a configurable env var `GEMINI_MODEL`, defaulting to the maintained alias `gemini-flash-latest`. **Verify at build time** which concrete Flash model and free-tier limits apply to the account/region; do not hardcode a version. Learner choice, accepted tradeoff: a hosted free-tier API instead of a local model (no large download, no heavy RAM use).

## Where It Runs and How Someone Tries It

- Runs **locally** as a Streamlit app; deployment is optional and not required (`scope.md > POC Boundary`, `prd.md > Non-Goals`).
- Environment: Python 3.10+, a free `GEMINI_API_KEY` in a local `.env` (never committed).
- Start command: `streamlit run app.py`
- What to open: the browser page Streamlit prints (usually http://localhost:8501).
- For the required demo video: paste a set of notes, generate, answer, submit, and show the day-by-day plan — one full run in about a minute (`prd.md > The Core Journey`).
- Submission needs a short demo video and a public GitHub repository; the local recording is sufficient.

## Look and Feel

Carried forward from `prd.md > Look and Feel`; implementable with standard Streamlit plus a small block of custom CSS.

- **Palette:** off-white / very light gray page background, dark navy body text, green primary accent for buttons and positive feedback, subtle neutral borders for section separation.
- **Type:** a clean sans-serif (Streamlit's default sans-serif is fine); clear heading hierarchy; comfortable spacing.
- **Layout:** single column, vertical, responsive; each section (form, quiz, results, schedule) inside a bordered card (`st.container(border=True)`).
- **Schedule as the highlight:** a clear heading, a short weak-topics line, and a well-spaced day-by-day table (`st.dataframe` or a styled list). Subtle green accents separate priority ("weak") rows from lighter ("review") rows.
- **Tone:** calm, academic, student-friendly. Minimal decoration — no gradients, animations, or decorative icons.
- **Styling limits:** Streamlit styling is done by injecting a small CSS block; we keep it lightweight and avoid anything that fights the default layout. No separate frontend framework (`prd.md > Product Decisions`).

## Components

### `app.py` — the Streamlit page

Draws the single page, owns all `st.session_state`, wires button clicks to the deterministic modules and the AI helper, and renders the quiz, results, and schedule. It contains no grading, date, or scheduling math itself.
PRD refs: `prd.md > Screens and Layout`, `prd.md > States and Boundaries`, `prd.md > The Core Journey`.

### `ai_client.py` — Gemini integration

Creates the `google-genai` client from `GEMINI_API_KEY`, reads the model name from `GEMINI_MODEL`, and exposes two functions:

- `generate_quiz(notes) -> dict` — asks for exactly five questions matching the quiz schema; returns parsed JSON.
- `suggest_tasks(topics) -> dict` — after grading, asks for a short revision task per weak topic. It is called only when weak topics exist; an all-correct run skips it.

Both use structured output (`response_mime_type="application/json"` with a `response_schema`) and low temperature for steadiness. Both raise a single, catchable error type (e.g., `AiError`) on API failure, rate limit, or unusable output. It performs **no** grading or date logic.
PRD refs: `prd.md > Quiz generation`, `prd.md > Product Decisions` (division of responsibility).

### `validators.py` — input checks

Plain functions: `validate_notes(notes)`, `validate_exam_date(exam_date, today)`, `validate_hours(hours)`, and a small `validate_inputs(...)` that runs all three and returns any error messages. `today` is supplied explicitly (the local date) rather than read inside the function, so tests can fix it. Encodes the exact PRD rules: ≥100 trimmed characters, exam date strictly after today, hours from 0.5 through 12 inclusive.
PRD ref: `prd.md > Input form and validation`.

### `quiz_logic.py` — schema check, grading, weak topics

- `validate_quiz(raw) -> (ok, quiz_or_error)` — enforces exactly five questions; each with nonempty question text, nonempty topic, four unique nonempty options, a `correct_index` that is a true integer (not a Boolean) within 0–3, and a nonempty explanation. Any malformed response, invalid field, or wrong question count is rejected before the quiz is stored.
- `grade_quiz(quiz, answers) -> (score, per_question)` — compares each selected index to `correct_index`.
- `find_weak_topics(quiz, per_question) -> list` — groups incorrect topics and orders by mistake count, descending.

Pure Python, no AI.
PRD refs: `prd.md > Quiz generation`, `prd.md > Results`.

### `schedule.py` — the deterministic plan builder

`build_schedule(weak_topics, all_topics, task_suggestions, exam_date, today, daily_hours) -> list[row]`. It:

- builds dates from the supplied local `today` to the day before `exam_date` (day 1 is today),
- orders topics with weak topics first, then lighter review; when there are no weak topics, produces a balanced plan across topics without inventing weak ones,
- attaches a task (from `task_suggestions`, else a plain fallback text derived from the topic),
- assigns `minutes` per day so the daily total never exceeds `daily_hours * 60`,
- never emits a task on or after the exam day,
- returns an empty list with a clear reason if there are no valid study days (defensive; shouldn't occur given the date rule).

`today` is a parameter so tests can fix the date.
PRD ref: `prd.md > Revision schedule`.

## Data Model

No database and no persistence (`scope.md > Explicitly Cut`). Everything lives in `st.session_state` for the current session and is discarded when the app restarts. Each piece: where it lives, how it updates, and what happens on return.

**Quiz schema (from the AI, validated before storing)** — `prd.md > Quiz generation`:

```json
{
  "questions": [
    {
      "question": "Question text?",
      "topic": "Cell Respiration",
      "options": ["A", "B", "C", "D"],
      "correct_index": 2,
      "explanation": "Why the correct option is right."
    }
  ]
}
```

**Task suggestions (from the AI, validated)** — `prd.md > Revision schedule`:

```json
{ "tasks": [ { "topic": "Cell Respiration", "task": "Review the steps of respiration." } ] }
```

**Session state keys** (all in `app.py`):

| Key | Holds | Updated when | On return (rerun) |
|---|---|---|---|
| `quiz` | list of 5 validated question dicts | Generate Quiz succeeds | Reused as-is; no new AI call |
| `answers` | list of 5 ints or `None` | a radio option is selected | Preserved by the widget key |
| `submitted` | bool | Submit Answers succeeds | Stays true; answers locked |
| `score` | int 0–5 | on submit | Reused; not recomputed |
| `per_question` | list of `{correct, selected_index, correct_index}` | on submit | Reused |
| `weak_topics` | list of `{topic, mistakes}` (desc) | on submit | Reused |
| `schedule` | list of schedule rows | on submit | Reused |
| `schedule_status` | `"done"` / `"fallback"` / `None` | on submit | Reused; never regenerated on rerun |
| `ui_error` | string or `None` | validation / API / schema errors | Cleared on Start Over |
| `ai_pending` | bool | during an API call | Drives the loading/disabled state |

**Calls are button-guarded.** The UI has three actions — **Generate Quiz**, **Submit Answers**, and **Start Over**. Each API call is triggered only inside its own button's handler: `generate_quiz` only on Generate Quiz, and `suggest_tasks` only on Submit Answers (and only when weak topics exist). Submitted results, `weak_topics`, `schedule`, and `schedule_status` are stored in `st.session_state` when they are computed, so an ordinary Streamlit rerun reads them back instead of calling Gemini again.

**Schedule row** — `prd.md > Revision schedule`:

```json
{ "day": 1, "date": "2026-10-15", "topic": "Cell Respiration", "priority": "weak", "task": "Review respiration steps", "minutes": 60 }
```

`priority` is only `"weak"` or `"review"`; `minutes` is a positive integer set by Python.

## File Structure

```
StudySprint AI/
├── app.py              # Streamlit page: layout, session state, wiring
├── ai_client.py        # Gemini calls (quiz + task suggestions), JSON parsing
├── quiz_logic.py       # schema validation, grading, weak-topic grouping
├── schedule.py         # dates, day numbers, minutes, daily-limit enforcement
├── validators.py       # notes / exam-date / hours input validation
├── tests/
│   ├── test_validators.py
│   ├── test_quiz_logic.py
│   ├── test_schedule.py
│   └── test_ai_client.py   # mocked Gemini: success, malformed, invalid, error, rate limit
├── requirements.txt    # streamlit, google-genai, python-dotenv, pytest
├── .env.example        # GEMINI_API_KEY, GEMINI_MODEL (names only, no secrets)
├── .gitignore          # .env, venv, __pycache__, .pytest_cache
├── README.md           # how to run it
└── devpost/            # planning docs (this workspace)
```

## External Services and Dependencies

### Google Gemini API

- **SDK / import:** `pip install google-genai`; `from google import genai`, `from google.genai import types`.
- **Auth:** `client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])` (the SDK also auto-reads `GEMINI_API_KEY` / `GOOGLE_API_KEY`). Key from Google AI Studio; stored in `.env` locally, never committed.
- **Model:** `os.environ.get("GEMINI_MODEL", "gemini-flash-latest")` — configurable.
- **Structured call shape:** `client.models.generate_content(model=..., contents=<prompt+notes>, config=types.GenerateContentConfig(response_mime_type="application/json", response_schema=<schema>, temperature=0.4))`, then read the parsed JSON. Prompt must not duplicate the schema.
- **Cost:** free tier on Google AI Studio. **Unverified:** current model name and free-tier rate limits — confirm at build.
- **Docs:** https://ai.google.dev/gemini-api/docs · https://googleapis.github.io/python-genai/

### Python libraries

- `streamlit`, `google-genai`, `python-dotenv`, `pytest` — all free and pip-installable. No database, no cloud storage, no auth provider.

## Testing

`pytest`, deterministic, no real API calls (`prd.md > States and Boundaries`).

- **`test_validators.py`** — empty / too-short notes; exam date today and in the past (with `today` supplied explicitly); hours below 0.5, above 12, and missing.
- **`test_quiz_logic.py`** — correct and incorrect answers; score out of five; weak-topic grouping ordered by descending mistakes; the all-correct case; rejection of malformed quizzes (wrong count, duplicate options, `correct_index` out of range, a Boolean `correct_index`, empty fields).
- **`test_schedule.py`** — starts today, ends the day before the exam, correct day numbering, no tasks on/after the exam date, daily minutes never exceed the limit, and the single-study-day case. `today` is passed in, so the tests don't depend on the real clock.
- **`test_ai_client.py`** — **monkeypatch the SDK** to simulate: a valid response (parsing works), malformed JSON, invalid quiz data, an API error, and a rate-limit error (each raises `AiError`). No API key required.

The whole suite runs with `pytest` before the build is considered done.

## Important Failure Modes

- **Gemini slow, down, or rate-limited** → catch `AiError`, show a friendly "try again" message, keep the user's inputs, store nothing (`prd.md > States and Boundaries`).
- **Malformed JSON or invalid quiz schema** → reject the entire response, offer retry, never show a partial or invented quiz.
- **Invalid inputs** → inline message beside the field; no API call is made.
- **Schedule-generation problem** (e.g., the task-suggestion call fails) → Python still builds a valid plan using plain fallback task text; if even the date range is unusable, show a clear message instead of an invalid schedule.
- **Duplicate API calls on reruns** → the quiz and results live in `st.session_state`; the AI is called only from the Generate and (post-submit) task-suggestion actions, never during a plain rerun.

## What Was Simplified and Why

- **No database and no persistence** — a single run produces one plan; state lives only in the session (`scope.md > Explicitly Cut`).
- **Local run instead of deployment** — a recorded local demo satisfies the submission; deployment adds no product proof (`prd.md > Non-Goals`).
- **Pasted text instead of file upload** — proves the same workflow without upload handling (`prd.md > Deferred From the POC`).
- **A single Streamlit page instead of multiple screens** — the one-run loop needs no navigation.
- **One AI "task suggestion" call with a deterministic fallback** — keeps the approved quiz schema untouched and the schedule robust; a failure degrades to plain Python task text rather than a broken plan.

## Decisions and Open Issues

**Learner choices** (with accepted tradeoff):

- Gemini API via `google-genai`, configurable model name — hosted free tier instead of a local model (`prd.md > Product Decisions`).
- Small module split (page / AI helper / deterministic modules) — a few more files for isolated, testable logic.
- Quiz and schedule schemas as documented above — `correct_index` for reliable grading.
- `st.session_state` for the whole run, plus a **Start Over** button — no persistence, no DB.
- API calls are guarded by their own button actions and cached in `st.session_state`, so reruns never trigger duplicate calls; an all-correct run skips the task-suggestion call.
- `pytest` with mocked Gemini responses and an injected local `today` — deterministic tests without real API calls (`prd.md > States and Boundaries`).

**One genuine learner uncertainty, discussed:** how to test code that calls an external API without real calls. Clarified with the **mocking/stub** approach — replace the SDK call with a fake that returns canned success, malformed, and error responses. The build will demonstrate this in `test_ai_client.py`.

**Open issues:**

- **Confirm during implementation (non-blocking; do not delay the build):** the current Gemini Flash model name and free-tier rate limits for the account/region. The model stays configurable through `GEMINI_MODEL` (default alias `gemini-flash-latest`), so this can be verified and adjusted as the integration is written.
- **Revision-task approach — approved:** a second Gemini call after grading (`suggest_tasks`) generates task text when weak topics exist; an all-correct run skips it. Python's `schedule.py` owns dates, day numbers, and the daily time limit, with a deterministic fallback task text if the call fails.
