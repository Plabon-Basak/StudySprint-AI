"""Deterministic quiz logic for StudySprint AI — no AI, no Streamlit.

Implements `prd.md > Quiz generation` (schema validation) and
`prd.md > Results` (scoring and weak-topic grouping). Everything here is plain
Python so the tests are exact and the output is always the same for the same
input.
"""

QUESTIONS_PER_QUIZ = 5
OPTIONS_PER_QUESTION = 4


def _nonempty_str(value):
    return isinstance(value, str) and value.strip() != ""


def validate_quiz(raw):
    """Check a raw quiz from the AI.

    Returns (True, quiz) where `quiz` is a list of five cleaned question dicts,
    or (False, message) when the response does not match the schema.
    """
    if not isinstance(raw, dict):
        return False, "Quiz response was not an object."

    questions = raw.get("questions")
    if not isinstance(questions, list) or len(questions) != QUESTIONS_PER_QUIZ:
        return False, f"Quiz must contain exactly {QUESTIONS_PER_QUIZ} questions."

    quiz = []
    for number, question in enumerate(questions, start=1):
        cleaned = _validate_question(question, number)
        if isinstance(cleaned, str):
            return False, cleaned
        quiz.append(cleaned)
    return True, quiz


def _validate_question(question, number):
    """Return a cleaned question dict, or an error message string."""
    if not isinstance(question, dict):
        return f"Question {number} is not an object."
    if not _nonempty_str(question.get("question")):
        return f"Question {number} is missing its text."
    if not _nonempty_str(question.get("topic")):
        return f"Question {number} is missing its topic."
    if not _nonempty_str(question.get("explanation")):
        return f"Question {number} is missing its explanation."

    options = question.get("options")
    if not isinstance(options, list) or len(options) != OPTIONS_PER_QUESTION:
        return f"Question {number} must have exactly {OPTIONS_PER_QUESTION} options."
    cleaned_options = []
    for option in options:
        if not _nonempty_str(option):
            return f"Question {number} has an empty option."
        cleaned_options.append(option.strip())
    if len(set(cleaned_options)) != OPTIONS_PER_QUESTION:
        return f"Question {number} has duplicate options."

    correct_index = question.get("correct_index")
    if isinstance(correct_index, bool) or not isinstance(correct_index, int):
        return f"Question {number} has an invalid correct answer."
    if not 0 <= correct_index < OPTIONS_PER_QUESTION:
        return f"Question {number} has an out-of-range correct answer."

    return {
        "question": question["question"].strip(),
        "topic": question["topic"].strip(),
        "options": cleaned_options,
        "correct_index": correct_index,
        "explanation": question["explanation"].strip(),
    }


def grade_quiz(quiz, answers):
    """Return (score, per_question) for the student's answers.

    `answers` is a list of selected option indices (ints), or None for a
    question that was not answered.
    """
    per_question = []
    score = 0
    for index, question in enumerate(quiz):
        selected = answers[index] if index < len(answers) else None
        correct = selected == question["correct_index"]
        if correct:
            score += 1
        per_question.append(
            {
                "index": index,
                "correct": correct,
                "selected_index": selected,
                "correct_index": question["correct_index"],
            }
        )
    return score, per_question


def find_weak_topics(quiz, per_question):
    """Collect the topics of wrong answers, ordered by mistakes (most first).

    Topics with the same mistake count are ordered alphabetically so the result
    is always the same.
    """
    counts = {}
    for question, result in zip(quiz, per_question):
        if not result["correct"]:
            topic = question["topic"]
            counts[topic] = counts.get(topic, 0) + 1

    ordered = sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    return [{"topic": topic, "mistakes": mistakes} for topic, mistakes in ordered]
