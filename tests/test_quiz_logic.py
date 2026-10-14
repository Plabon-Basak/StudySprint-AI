"""Tests for quiz_logic: schema validation, scoring, weak-topic detection."""

import quiz_logic


def _valid_raw_quiz():
    return {
        "questions": [
            {
                "question": f"Question {i}?",
                "topic": f"Topic {i}",
                "options": ["Option A", "Option B", "Option C", "Option D"],
                "correct_index": i % 4,
                "explanation": f"Because {i}.",
            }
            for i in range(1, 6)
        ]
    }


def _gradable_quiz():
    ok, quiz = quiz_logic.validate_quiz(_valid_raw_quiz())
    assert ok
    return quiz


def test_valid_quiz_passes():
    ok, quiz = quiz_logic.validate_quiz(_valid_raw_quiz())
    assert ok is True
    assert isinstance(quiz, list)
    assert len(quiz) == 5


def test_rejects_non_object():
    ok, message = quiz_logic.validate_quiz("nope")
    assert ok is False
    assert isinstance(message, str)


def test_rejects_missing_questions_key():
    ok, _ = quiz_logic.validate_quiz({})
    assert ok is False


def test_rejects_wrong_question_count():
    for count in (4, 6):
        raw = _valid_raw_quiz()
        questions = raw["questions"]
        raw["questions"] = questions[:count] if count <= 5 else questions + [questions[0]]
        ok, _ = quiz_logic.validate_quiz(raw)
        assert ok is False, f"expected {count} questions to be rejected"


def test_rejects_duplicate_options():
    raw = _valid_raw_quiz()
    raw["questions"][0]["options"] = ["Same", "Same", "Option C", "Option D"]
    ok, _ = quiz_logic.validate_quiz(raw)
    assert ok is False


def test_rejects_wrong_option_count():
    raw = _valid_raw_quiz()
    raw["questions"][0]["options"] = ["Option A", "Option B", "Option C"]
    ok, _ = quiz_logic.validate_quiz(raw)
    assert ok is False


def test_rejects_empty_fields():
    for field in ("question", "topic", "explanation"):
        raw = _valid_raw_quiz()
        raw["questions"][0][field] = "   "
        ok, _ = quiz_logic.validate_quiz(raw)
        assert ok is False, f"expected empty {field} to be rejected"


def test_rejects_empty_option():
    raw = _valid_raw_quiz()
    raw["questions"][0]["options"][2] = ""
    ok, _ = quiz_logic.validate_quiz(raw)
    assert ok is False


def test_rejects_out_of_range_correct_index():
    for bad in (-1, 4):
        raw = _valid_raw_quiz()
        raw["questions"][0]["correct_index"] = bad
        ok, _ = quiz_logic.validate_quiz(raw)
        assert ok is False, f"expected correct_index {bad} to be rejected"


def test_rejects_boolean_correct_index():
    raw = _valid_raw_quiz()
    raw["questions"][0]["correct_index"] = True
    ok, _ = quiz_logic.validate_quiz(raw)
    assert ok is False


def test_rejects_non_integer_correct_index():
    for bad in (2.0, "2", None):
        raw = _valid_raw_quiz()
        raw["questions"][0]["correct_index"] = bad
        ok, _ = quiz_logic.validate_quiz(raw)
        assert ok is False, f"expected correct_index {bad!r} to be rejected"


def test_grade_all_correct():
    quiz = _gradable_quiz()
    answers = [question["correct_index"] for question in quiz]
    score, per_question = quiz_logic.grade_quiz(quiz, answers)
    assert score == 5
    assert all(result["correct"] for result in per_question)


def test_grade_all_wrong():
    quiz = _gradable_quiz()
    answers = [(question["correct_index"] + 1) % 4 for question in quiz]
    score, per_question = quiz_logic.grade_quiz(quiz, answers)
    assert score == 0
    assert not any(result["correct"] for result in per_question)


def test_grade_partial():
    quiz = _gradable_quiz()
    answers = [question["correct_index"] for question in quiz]
    answers[0] = (answers[0] + 1) % 4
    answers[3] = (answers[3] + 1) % 4
    score, per_question = quiz_logic.grade_quiz(quiz, answers)
    assert score == 3
    assert [result["correct"] for result in per_question] == [False, True, True, False, True]


def test_grade_handles_missing_answers():
    quiz = _gradable_quiz()
    score, per_question = quiz_logic.grade_quiz(quiz, [])
    assert score == 0
    assert all(result["selected_index"] is None for result in per_question)


def test_weak_topics_grouped_and_ordered():
    quiz = [
        {"topic": "Alpha", "correct_index": 0},
        {"topic": "Beta", "correct_index": 0},
        {"topic": "Alpha", "correct_index": 1},
        {"topic": "Gamma", "correct_index": 2},
        {"topic": "Beta", "correct_index": 3},
    ]
    per_question = [{"index": i, "correct": False} for i in range(5)]
    weak = quiz_logic.find_weak_topics(quiz, per_question)
    assert weak == [
        {"topic": "Alpha", "mistakes": 2},
        {"topic": "Beta", "mistakes": 2},
        {"topic": "Gamma", "mistakes": 1},
    ]


def test_weak_topics_empty_when_all_correct():
    quiz = [
        {"topic": "Alpha", "correct_index": 0},
        {"topic": "Beta", "correct_index": 1},
    ]
    per_question = [{"index": 0, "correct": True}, {"index": 1, "correct": True}]
    assert quiz_logic.find_weak_topics(quiz, per_question) == []
