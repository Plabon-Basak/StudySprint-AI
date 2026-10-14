---
doc: prd
status: approved
---

# StudySprint AI — Product Requirements

An adaptive revision coach for university students: paste study notes, take a five-question quiz, and get a personalized revision plan built from what you got wrong.
Source: `scope.md > The Core Loop`, `scope.md > The Unique Kernel`.

## The Core Journey

The complete path, end to end, on one page.

1. The student opens StudySprint AI. They see the title, a short description, an empty input form (study-notes text area, exam-date picker, daily-study-hours input, and a "Generate Quiz" button), and a subtle hint below the form: "Your personalized quiz, results, and revision plan will appear here after you generate your quiz."
2. They paste their study notes into the text area (at least 100 characters after trimming).
3. They choose an exam date that is strictly after today.
4. They set their available daily study hours (default 2; valid from 0.5 through 12 inclusive, fractional allowed).
5. They click **Generate Quiz**. Inputs are validated first; if anything is invalid, an inline message appears and no quiz is generated and no AI call is made. While the request is processing, the button is disabled and a simple loading indicator shows.
6. Five multiple-choice questions appear below the form on the same page. Each shows its question text, a small topic label, and four labeled options as radio buttons (exactly one selectable per question). No correct answers or explanations are shown yet.
7. The student answers all five questions and clicks **Submit Answers**. If any question is unanswered, a clear validation message appears and submission is blocked.
8. Results appear on the same page: a total score out of five, each question marked correct or incorrect, the correct answer and a short explanation for every question, and a weak-topics summary.
9. Below the results, the revision schedule appears: a day-by-day plan from today (the student's local date) through the day before the exam, with weak topics prioritized. Day 1 is today, not tomorrow. This is the "oh, that's cool" beat — the quiz results turned into a concrete day-by-day plan.
Source: `scope.md > What "Working" Looks Like`, `scope.md > The Core Loop`.

## Screens and Layout

One surface, no navigation. A single-page, vertically organized interface.

- Top: the title "StudySprint AI" and a short description: "Turn your study notes into a focused quiz and a personalized revision plan."
- Input section: study-notes text area, exam-date picker, daily-study-hours numeric input, and a "Generate Quiz" button.
- Empty state: below the form, the hint "Your personalized quiz, results, and revision plan will appear here after you generate your quiz." No fake questions, sample scores, or fabricated plan.
- Quiz section: the five questions with topic labels and radio options, then a single "Submit Answers" button.
- Results section: score, per-question feedback, and weak-topics summary.
- Revision schedule section: the day-by-day plan, presented as the visual highlight.

Sections are grouped in simple cards or bordered areas. No sidebar, no login screen, no multiple-page navigation.
Source: `scope.md > The POC Boundary`.

## Look and Feel

A calm, modern academic style — focused, trustworthy, student-friendly.

- **Colors:** light off-white to very light gray background; dark navy text; green as the primary accent for buttons, progress indicators, and positive feedback. Subtle neutral borders/backgrounds separate sections.
- **Typography:** clean, readable sans-serif; clear heading hierarchy; comfortable spacing.
- **Layout:** single-page, vertical, responsive on desktop and mobile; simple cards or bordered sections grouping the form, quiz, results, and schedule.
- **Revision schedule emphasis:** a clear heading, a short weak-topics summary, and a well-spaced day-by-day table or list. Subtle green accents distinguish priority revision tasks from lighter review tasks.
- **Quiz and results:** questions easy to scan, options easy to select, feedback clear. Restrained indicators for correct/incorrect answers with readable explanations.
- **Overall:** polished but minimal. Avoid excessive gradients, flashy animations, oversized graphics, unnecessary icons, and generic chatbot styling. Prioritize readability and accessibility over decoration.
Source: `scope.md > Inspiration & Identity`.

## Features and Behavior

### Input form and validation

- The study-notes text area is trimmed and must contain at least 100 characters. If empty or too short, show inline: "Please paste at least 100 characters of study notes so StudySprint AI can create a useful quiz." The existing input is preserved.
- The exam date must be strictly after today. If today or earlier is chosen, show inline: "Please choose an exam date at least one day from today so we can build your revision plan." No quiz is generated until the date is valid (avoids a no-days-left flow).
- Daily study hours is required, defaults to 2, and accepts values from 0.5 through 12, inclusive, including reasonable fractions (e.g., 1.5). Blank, zero, negative, nonnumeric, values below 0.5, or values above 12 are rejected with inline: "Enter daily study time between 0.5 and 12 hours."
- Validation messages appear near the relevant fields; all other inputs stay intact after an error.
- No AI call is made while inputs are invalid.
- Repeated submissions are disabled while a request is processing, with a simple loading indicator.

### Quiz generation

- Exactly five multiple-choice questions, each with: question text, four options, one correct answer, a short explanation, and a concise topic label (e.g., "Cell Respiration").
- Topic labels are specific enough to guide revision and consistent across questions about the same concept.
- The AI returns structured data matching a defined schema. Before display, the response is validated: exactly five questions; each with nonempty question text, a nonempty topic label, exactly four unique options, exactly one valid correct-answer reference, and a nonempty explanation.
- Malformed or incomplete responses are rejected in full — the student sees a clear error with a retry option, and no partial or invented quiz is shown.
- The topic label is metadata generated from the supplied notes, not proof the question is factually correct.

- [ ] Clicking Generate Quiz with valid inputs produces exactly five questions, each showing four unique options and a topic label.
- [ ] A malformed or incomplete AI response is rejected and a retry is offered; no partial quiz is displayed.

### Answering and submission

- All five questions are shown together; each uses radio buttons allowing exactly one selection.
- One "Submit Answers" button sits below all five questions.
- All five must be answered before submitting; otherwise a clear validation message appears.
- Correct answers and explanations are never displayed before submission, even if they are retained internally for scoring.

- [ ] Submitting with any unanswered question is blocked and shows a message.
- [ ] No correct answers or explanations are displayed before submission.
- [ ] After a valid submit, answers can no longer be changed.

### Results

- Total score out of five.
- Each question marked correct or incorrect, with the correct answer and a short explanation shown for every question.
- A small, subtle topic label appears beside or below each question.
- Weak-topic detection: selected answers are compared with correct answers; the topic labels of incorrect answers are collected; questions sharing a topic label are grouped and mistakes counted per topic.
- The weak-topics summary is ordered by number of mistakes, most to fewest.
- If every answer is correct, show a positive message such as "Great work! No weak topics were identified in this quiz." No weak topics are invented.

- [ ] Score equals the number of correct answers, out of five.
- [ ] Each incorrect question is flagged and shows the correct answer and explanation.
- [ ] The weak-topics summary lists topics in descending mistake order.
- [ ] An all-correct run shows the positive message and no invented weak topics.

### Revision schedule

The kernel of the product — the decision about what to revise next.

- A day-by-day list or table ordered chronologically from today (the student's local date) through the day before the exam. Day 1 is today, not tomorrow. No tasks fall on exam day or afterward.
- Each row contains: **Day and date** (e.g., "Day 1 — October 15"), **study task** (a specific topic or revision activity), and **suggested time** (estimated study time, kept within the available daily hours).
- Weak topics are prioritized and scheduled for focused revision, including a short practice or self-review task where appropriate.
- Correctly answered topics may receive lighter review if time permits.
- Exam date and daily hours determine schedule length and task distribution. If there are no incorrect answers, a balanced review plan is created instead of inventing weak topics.
- When only one study day is available (the exam is tomorrow), the schedule still produces a usable single-day plan.
- Python validates and enforces each day's planned study time against the student's daily limit. The AI may suggest revision tasks, but it is not trusted to enforce the time constraint on its own.

- [ ] The schedule starts today (Day 1 is today) and ends the day before the exam, with no tasks on or after exam day.
- [ ] Each row shows a day/date, a study task, and a suggested time.
- [ ] Topics from incorrect answers appear before lighter-review topics.
- [ ] The daily suggested time never exceeds the student's available daily hours, and this is enforced in Python.
- [ ] With only one study day available, a usable single-day plan is still produced.
Source: `scope.md > The Unique Kernel`, `scope.md > What "Working" Looks Like`.

## States and Boundaries

- **First use / empty state** — the form plus the hint beneath it; nothing fabricated is shown.
- **Input error states** — inline messages near the offending field for short notes, an exam date at or before today, and out-of-range daily hours; all other inputs preserved; no AI call.
- **Processing state** — submit is disabled and a simple loading indicator shows.
- **AI failure state** — a friendly retry message is shown instead of fabricated results.
- **Success state** — quiz, results, and revision schedule render on the same page.
- **Persistence** — none. The loop is single-session: one run produces one plan; closing the app discards everything.
Source: `scope.md > The Core Loop`, `scope.md > Explicitly Cut`.

## Product Decisions

- Single-page vertical layout; quiz, results, and schedule render below the input form with no navigation — keeps the one-run loop frictionless.
- All five questions shown at once with one Submit button; no timers or question-by-question navigation — simplest flow that still proves the kernel.
- Answers/explanations hidden until submission — the plan depends on honest results.
- Study notes must be at least 100 characters — enough text for the AI to build a useful quiz.
- Exam date must be strictly after today — guarantees a meaningful schedule and removes a special no-days-left flow.
- Daily study hours default 2, valid from 0.5 through 12 inclusive with fractions allowed — practical, realistic limits.
- Every question carries an AI-assigned topic label — the bridge from wrong answers to the revision plan.
- Weak topics ordered by mistake count; no weak topics invented when everything is correct.
- **Division of responsibility:** the AI generates questions, explanations, topic labels, and suggests revision tasks; the application (Python) validates the quiz, enforces the date range and each day's planned study time against the daily limit, and keeps scoring and weak-topic counting deterministic. The AI is not trusted to enforce the time constraint on its own. Chosen for reliability and a predictable schedule.
- Structured, schema-validated AI output, checked before display — prevents malformed quizzes from reaching the student.
- Visual direction: calm academic palette (off-white background, navy text, green accent), sans-serif type, section cards, with the revision schedule as the visual highlight.
- Styling must be achievable with standard Streamlit components plus lightweight custom CSS; no separate frontend framework.
Source: `scope.md > The POC Boundary`, `scope.md > Explicitly Cut`.

## What We're Building

The full six-step loop on a single page: paste notes → exam date and daily hours → generate five MCQs (with topic labels) → answer and submit → score, weak topics, and explanations → a day-by-day revision schedule that prioritizes weak topics within the available time.

## Deferred From the POC

- **File uploads / other note formats** — pasted text proves the same workflow without upload handling (`scope.md > Later`).
- **Progress tracking across sessions** — history is a product feature, not part of notes → quiz → plan (`scope.md > Explicitly Cut`).
- **Larger question banks / repeated quizzes over time** — a single run proves the kernel (`scope.md > Later`).

## Possible Later Enhancements

- Let students re-quiz on weak topics to verify improvement.
- Support notes in additional formats (PDF, DOCX) via file upload.
- Persist plans and progress across sessions so students can track revision over days.

## Non-Goals

- **User accounts / login** — not needed to prove the kernel.
- **Database / any persistence** — nothing must persist for one run.
- **Calendar integrations, reminders, notifications** — out of scope; the plan is a static day-by-day list.
- **Deployment** — a reliable local demo is acceptable.
- **Topic-management system or advanced analytics** — the AI assigns labels; no management UI.
- **Timers, question-by-question navigation, gamification** — unnecessary for the proof.

## Open Questions

- None blocking `4-spec`. The AI provider and API key are undecided and belong to `4-spec`; the learner has prior Gemma/StudyMate AI experience that may inform the choice (`learner-profile.md > Notes and Open Questions`).
