---
doc: scope
status: approved
---

# StudySprint AI

An adaptive revision coach: paste study notes, take a five-question quiz, and get a personalized revision plan built from what you got wrong.

## The Unique Kernel

The quiz isn't the product — the decision about what to revise next is. A generic quiz generator tests understanding; StudySprint connects assessment to an actionable revision plan. If you deleted the schedule, nobody would notice the difference from a plain "quiz me on this text" prompt — so the schedule stays at the center.

## Who It's For

A university student — the learner himself first — prepping for an exam with a pile of notes and limited days left. Today he'd paste notes into a chatbot, get some questions, and still have to decide himself what to revisit and when. StudySprint makes that decision for him.

## The Core Loop

Paste notes → enter exam date and daily study hours → generate five multiple-choice questions → answer and submit → see score, weak topics, and explanations → get a revision schedule that prioritizes weak topics and fits the time before the exam. The loop is single-session: one run produces one plan.

## Inspiration & Identity

The learner is inspired by AI learning tools that turn study material into interactive quizzes with explanations — "combining the usefulness of ChatGPT with the structure of a personalized study planner." Practical, student-built, not overloaded with features. Follows his prior StudyMate AI work (Best Use of Gemma, Hacktoberfest Hack Day Dinajpur).

## Why This Matters to the Learner

In his words: "As a student, I understand that preparing for exams, organizing study materials, and figuring out which topics need more revision can be challenging... I want to build something useful for students like me." He wants something simple, practical, and genuinely useful — and something he would personally use.

## What "Working" Looks Like

A student opens StudySprint AI and completes one full run in about a minute:

1. Paste study notes into a text area.
2. Enter exam date and hours available per day.
3. Click to generate five four-option multiple-choice questions.
4. Answer and submit.
5. See score, incorrectly answered topics, and explanations of the correct answers.
6. See a simple day-by-day list of study tasks that prioritizes weak topics and considers the exam date and available daily study hours.

The "oh, that's cool" beat: step 6 — the moment the quiz results turn into a concrete day-by-day plan.

## The POC Boundary

In: the six steps above, one full workflow in a single session, running locally as a Streamlit app. The learner's stated stack: Python + Streamlit + an AI model API (provider undecided — decided in `4-spec`).

## Later

- File uploads and notes in other formats
- Progress tracking across sessions
- Larger question banks or repeated quizzes over time

## Explicitly Cut

- **User accounts** — no login needed to prove the kernel; a single-session prototype is enough.
- **Database** — nothing needs to persist for one run; cutting it keeps the demo reliable.
- **File uploads** — pasted text proves the same workflow without upload handling.
- **Long-term progress tracking** — history is a product feature, not part of notes → quiz → plan.
- **Deployment** — a reliable local demo is acceptable; deployment is optional for the hackathon.
