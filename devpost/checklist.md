---
doc: checklist
status: approved
---

# Build Checklist

Build mode: [learn or fast — record once chosen; carry forward on resume]

## Slices

- [ ] **1. The app runs and validates your inputs**
  Becomes usable: A running Streamlit app with the title, description, notes box, exam-date picker, daily-hours input, a Generate Quiz button, and the empty-state hint. Clicking Generate with bad input shows the exact inline messages; nothing else happens yet. All project setup — dependencies, virtual environment, config, and git — lands here.
  Why now: Bootstrapping lives inside slice one. A running app with real input validation is the first end-to-end behavior, and it confirms the toolchain (Python 3.14 + Streamlit) installs cleanly before we depend on it.
  PRD ref: `prd.md > Input form and validation`; `prd.md > Screens and Layout` (empty state)
  Spec ref: `spec.md > Components` (`app.py`, `validators.py`); `spec.md > File Structure`; `spec.md > Where It Runs and How Someone Tries It`
  Build: Create `requirements.txt`, `.env.example`, and a `.venv` on D:; install `streamlit` and `python-dotenv`. Write `validators.py` (notes ≥100 trimmed chars, exam date strictly after `today`, hours 0.5–12 inclusive, all taking an explicit `today`). Write `app.py` with the form, empty-state hint, and validation wiring. Write `tests/test_validators.py`.
  Verify (mechanical): `pytest tests/test_validators.py` passes; `streamlit run app.py` starts with no errors.
  Learner check: Open the app at http://localhost:8501 and click Generate with empty notes, a past-dated exam, and 0 hours; confirm the three inline messages appear. Confirm valid inputs currently do nothing yet.
  Commit: `Add app scaffold and input validation`

- [ ] **2. The deterministic brain grades a quiz and builds a schedule**
  Becomes usable: Plain-Python functions (no AI, no UI) that validate a quiz's shape, grade answers, group weak topics, and build a day-by-day schedule respecting the exam date and daily hours — proven by tests.
  Why now: The kernel — turning results into a revision plan — is the product, so its math must be proven first. It is pure Python, the safest thing to lock down before AI and UI touch it, and it delivers runnable test evidence (the spec's allowed single-layer exception).
  PRD ref: `prd.md > Quiz generation`; `prd.md > Results`; `prd.md > Revision schedule`
  Spec ref: `spec.md > Components` (`quiz_logic.py`, `schedule.py`); `spec.md > Data Model`
  Build: Implement `quiz_logic.validate_quiz/grade_quiz/find_weak_topics` and `schedule.build_schedule` (with an injected `today` and daily-limit enforcement). Write `tests/test_quiz_logic.py` and `tests/test_schedule.py`.
  Verify (mechanical): `pytest tests/test_quiz_logic.py tests/test_schedule.py` passes — score out of 5, descending weak-topic order, all-correct case, schema rejections (wrong count, duplicate options, out-of-range and Boolean `correct_index`, empty fields); schedule starts today, ends the day before the exam, correct day numbering, no tasks on/after exam day, daily minutes ≤ limit, single-study-day case.
  Learner check: Run `pytest -q`; all tests should pass. I'll print one generated schedule next to you so you can sanity-check the dates and minutes.
  Commit: `Add deterministic quiz and schedule logic with tests`

- [ ] **3. Gemini returns a valid five-question quiz (proven against the real API)**
  Becomes usable: `ai_client.generate_quiz(notes)` calls Gemini with structured output and returns a schema-shaped dictionary; `ai_client.suggest_tasks(topics)` returns task suggestions. Mocked tests cover the failure paths.
  Why now: The biggest unknown — an external API, structured output, and SDK compatibility on Python 3.14 — proven in isolation before the UI depends on it (risk-first).
  PRD ref: `prd.md > Quiz generation`; `prd.md > Product Decisions` (division of responsibility)
  Spec ref: `spec.md > Components` (`ai_client.py`); `spec.md > External Services and Dependencies`; `spec.md > Important Failure Modes`
  Build: Install `google-genai`. Implement `ai_client.py` with a configurable `GEMINI_MODEL`, an `AiError`, and `response_schema`-based structured output for both calls. Write `tests/test_ai_client.py` (mocked: success, malformed JSON, invalid quiz, API error, rate limit). Confirm the live model name and free-tier limits here.
  Verify (mechanical): `pytest tests/test_ai_client.py` passes with no real calls. Then one real inline `python -c` call using the key from `.env` returns five valid questions.
  Learner check: Put your free `GEMINI_API_KEY` in `.env` (I'll show the exact line). Run the live check command; confirm it prints five questions with topics. Your key is never committed.
  Commit: `Add Gemini client with structured output and mocked tests`

- [ ] **4. Generate a quiz in the app**
  Becomes usable: With valid inputs, clicking Generate Quiz calls Gemini and renders five questions, each with its topic label and four radio options — no correct answers shown. API/schema errors show a retry message instead.
  Why now: First moment the UI and the AI meet, delivering the visible quiz the rest of the journey depends on. Uses button-guarded calls and session state so reruns never double-call.
  PRD ref: `prd.md > Quiz generation`; `prd.md > Answering and submission` (display); `prd.md > States and Boundaries` (processing, AI failure)
  Spec ref: `spec.md > Data Model` (session state); `spec.md > Important Failure Modes`
  Build: In `app.py`, wire Generate → `validate_inputs` → `ai_client.generate_quiz` → `quiz_logic.validate_quiz` → store in `st.session_state`. Render questions with radio options; add the loading/disabled state; show a retry message on `AiError` or schema rejection.
  Verify (mechanical): App runs; a real generate shows five questions with four options each and no answers; selecting radios triggers no new API call (session-state reuse).
  Learner check: Paste real notes, click Generate, and confirm you see five questions with topic labels and four options, and no correct answers yet. Click a radio and confirm the quiz does not regenerate.
  Commit: `Generate and render the quiz from Gemini`

- [ ] **5. Answer, see results, and get your revision plan (the kernel payoff)**
  Becomes usable: Submit Answers → score out of five, correct/incorrect marks with explanations, a weak-topic summary, and the day-by-day revision schedule; answers lock after submit; Start Over resets. An all-correct run skips the task call and still shows a balanced plan.
  Why now: Closes the core journey and delivers the unique kernel — quiz results turned into a concrete plan — as the visible payoff the demo is built around.
  PRD ref: `prd.md > Answering and submission`; `prd.md > Results`; `prd.md > Revision schedule`; `prd.md > The Core Journey` (step 9)
  Spec ref: `spec.md > Components` (`quiz_logic.py`, `schedule.py`, `ai_client.py`); `spec.md > Data Model`; `spec.md > Look and Feel`
  Build: Wire Submit → grade → weak topics → (only if weak topics exist) `suggest_tasks` → `build_schedule`; render results and schedule from session state; lock answers; add Start Over; apply the calm academic styling with the schedule as the highlight.
  Verify (mechanical): App runs; a full run shows the score, per-question feedback, weak topics in descending order, and a schedule from today to the day before the exam with minutes ≤ the daily limit; an all-correct run skips the task call and shows the positive message plus a balanced plan; Start Over clears state.
  Learner check: Do one full run with real notes — generate, answer, submit — and confirm the schedule appears and feels like the highlight. Then try an all-correct run.
  Commit: `Add results, weak topics, and the revision schedule`

## Hands-on Checkpoints

- [ ] Early usable behavior explored — after Slice 4 (first time the quiz renders); feedback shapes the results/schedule rendering in Slice 5
- [ ] Final kick-the-tires exploration and feedback completed

## Final Review

- [ ] Final review complete — feedback resolved and learner confirms ready to ship

## Code Tour and App Map

- [ ] Learning activity complete — guided route, focused alternative, prior practice connected, or brief recap
- [ ] Optional edit and transfer reflection addressed — offered/declined/already covered/not applicable as appropriate
- [ ] `devpost/app-map.html` generated from finished code, checked, and shown, including a project-grounded practice to reuse

Activity and evidence: [pending]
Route and stops: [pending]
Edit outcome: [pending]
Reflection: [pending]
Activity mode: [pending]

## Revisions
