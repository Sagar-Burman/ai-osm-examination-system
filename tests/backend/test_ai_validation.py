import pytest

from app.models.question import Question
from app.services.ai_eval_service import _validate_ai_output


def make_question(max_marks=10):
    return Question(
        exam_id=1,
        question_number="2",
        question_text="Explain Machine Learning",
        max_marks=max_marks,
        rubric='[{"item":"Definition","marks":2}]',
        model_answer="Machine learning enables systems to learn from data.",
        is_optional=False,
    )


def valid_output(suggested_marks=8):
    return {
        "suggested_marks": suggested_marks,
        "max_marks": 10,
        "rubric_breakdown": [
            {"item": "Definition", "max": 2, "awarded": 2, "covered": True},
            {"item": "Types", "max": 2, "awarded": 2, "covered": True},
            {"item": "Applications", "max": 2, "awarded": 2, "covered": True},
            {"item": "Advantages", "max": 2, "awarded": 1, "covered": True},
            {"item": "Example", "max": 2, "awarded": 1, "covered": True},
        ],
        "strengths": ["Definition covered"],
        "missing_concepts": ["One advantage"],
        "summary": "Mostly complete answer.",
        "confidence": "medium",
        "ocr_concern": False,
    }


def test_valid_ai_output_is_accepted():
    result = _validate_ai_output(valid_output(8), make_question())

    assert result["suggested_marks"] == 8.0
    assert result["max_marks"] == 10.0


def test_ai_marks_cannot_exceed_question_max():
    payload = valid_output(14)
    payload["rubric_breakdown"][0]["awarded"] = 8
    payload["rubric_breakdown"][1]["awarded"] = 2
    payload["rubric_breakdown"][2]["awarded"] = 2
    payload["rubric_breakdown"][3]["awarded"] = 1
    payload["rubric_breakdown"][4]["awarded"] = 1

    with pytest.raises(ValueError, match="cannot exceed"):
        _validate_ai_output(payload, make_question())


def test_missing_ai_field_is_rejected():
    payload = valid_output(8)
    payload.pop("summary")

    with pytest.raises(ValueError, match="Missing AI fields"):
        _validate_ai_output(payload, make_question())


def test_rubric_total_must_equal_suggested_marks():
    payload = valid_output(9)

    with pytest.raises(ValueError, match="does not equal suggested marks"):
        _validate_ai_output(payload, make_question())
