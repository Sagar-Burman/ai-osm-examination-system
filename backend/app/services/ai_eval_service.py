import json
import os
import time

from fastapi import HTTPException, status
from google import genai
from google.genai import types

from app.core.config import GEMINI_MODEL
from app.models.ai_suggestion import AISuggestion
from app.models.answer_segments import AnswerSegment
from app.models.question import Question
from app.models.sheet import Sheet, SheetStatus


PROMPT_VERSION = "ai_eval_v1"


def _validate_ai_output(
    result: dict,
    question: Question
) -> dict:
    required_fields = {
        "suggested_marks",
        "max_marks",
        "rubric_breakdown",
        "strengths",
        "missing_concepts",
        "summary",
        "confidence",
        "ocr_concern"
    }

    missing = required_fields - set(result.keys())

    if missing:
        raise ValueError(
            f"Missing AI fields: {', '.join(sorted(missing))}"
        )

    try:
        suggested_marks = float(result["suggested_marks"])
        max_marks = float(result["max_marks"])
    except (TypeError, ValueError):
        raise ValueError(
            "suggested_marks and max_marks must be numeric"
        )

    if suggested_marks < 0:
        raise ValueError(
            "Suggested marks cannot be negative"
        )

    if suggested_marks > question.max_marks:
        raise ValueError(
            f"Suggested marks cannot exceed {question.max_marks}"
        )

    if max_marks != float(question.max_marks):
        raise ValueError(
            "AI max_marks does not match question max_marks"
        )

    rubric_breakdown = result["rubric_breakdown"]

    if not isinstance(rubric_breakdown, list):
        raise ValueError(
            "rubric_breakdown must be a list"
        )

    awarded_total = 0.0

    for item in rubric_breakdown:
        if not isinstance(item, dict):
            raise ValueError(
                "Each rubric breakdown item must be an object"
            )

        required_item_fields = {
            "item",
            "max",
            "awarded",
            "covered"
        }

        missing_item_fields = (
            required_item_fields - set(item.keys())
        )

        if missing_item_fields:
            raise ValueError(
                "Rubric item missing fields: "
                + ", ".join(sorted(missing_item_fields))
            )

        try:
            item_max = float(item["max"])
            awarded = float(item["awarded"])
        except (TypeError, ValueError):
            raise ValueError(
                "Rubric max and awarded values must be numeric"
            )

        if item_max < 0:
            raise ValueError(
                "Rubric item max cannot be negative"
            )

        if awarded < 0:
            raise ValueError(
                "Rubric awarded marks cannot be negative"
            )

        if awarded > item_max:
            raise ValueError(
                "Rubric awarded marks exceed item max"
            )

        if not isinstance(item["covered"], bool):
            raise ValueError(
                "Rubric covered must be boolean"
            )

        awarded_total += awarded

    if abs(awarded_total - suggested_marks) > 0.01:
        raise ValueError(
            "Rubric awarded total does not equal suggested marks"
        )

    if not isinstance(result["strengths"], list):
        raise ValueError(
            "strengths must be a list"
        )

    if not isinstance(result["missing_concepts"], list):
        raise ValueError(
            "missing_concepts must be a list"
        )

    if not isinstance(result["summary"], str):
        raise ValueError(
            "summary must be a string"
        )

    if not isinstance(result["confidence"], str):
        raise ValueError(
            "confidence must be a string"
        )

    if not isinstance(result["ocr_concern"], bool):
        raise ValueError(
            "ocr_concern must be boolean"
        )

    return {
        "suggested_marks": suggested_marks,
        "max_marks": max_marks,
        "rubric_breakdown": rubric_breakdown,
        "strengths": result["strengths"],
        "missing_concepts": result["missing_concepts"],
        "summary": result["summary"],
        "confidence": result["confidence"],
        "ocr_concern": result["ocr_concern"]
    }


def generate_ai_suggestion(
    db,
    sheet_id: int,
    question_id: int,
    examiner_id: int
):
    # ---------------------------------------------------------
    # Sheet
    # ---------------------------------------------------------
    sheet = (
        db.query(Sheet)
        .filter(Sheet.id == sheet_id)
        .first()
    )

    if sheet is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sheet not found"
        )

    if sheet.status != SheetStatus.IN_EVALUATION:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Sheet is not in evaluation"
        )

    # ---------------------------------------------------------
    # Question
    # ---------------------------------------------------------
    question = (
        db.query(Question)
        .filter(
            Question.id == question_id,
            Question.exam_id == sheet.exam_id
        )
        .first()
    )

    if question is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Question not found"
        )

    # ---------------------------------------------------------
    # OCR answer text
    # ---------------------------------------------------------
    segments = (
        db.query(AnswerSegment)
        .filter(
            AnswerSegment.sheet_id == sheet_id,
            AnswerSegment.question_id == question_id
        )
        .all()
    )

    answer_text_parts = []

    for segment in segments:
        text = (segment.text or "").strip()

        if text:
            answer_text_parts.append(text)

    answer_text = "\n".join(answer_text_parts).strip()

    if not answer_text:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="NO_ANSWER_TEXT"
        )

    # ---------------------------------------------------------
    # Rubric
    # ---------------------------------------------------------
    rubric = question.rubric

    if isinstance(rubric, str):
        try:
            rubric = json.loads(rubric)
        except json.JSONDecodeError:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Invalid question rubric"
            )

    if not isinstance(rubric, list):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid question rubric"
        )

    # ---------------------------------------------------------
    # Prompt
    # ---------------------------------------------------------
    prompt = f"""
You are the AI evaluation component of EvalAI.

Core principle:
AI assists. Humans decide.

Evaluate the student's answer using ONLY:
1. Question
2. Maximum marks
3. Rubric
4. Model answer
5. OCR-extracted student answer

Do not identify the student.

Do not invent facts outside the supplied answer.

Return ONLY valid JSON.
Do not return markdown.
Do not return explanations outside the JSON.

Question:
{question.question_text}

Maximum marks:
{question.max_marks}

Rubric:
{json.dumps(rubric, ensure_ascii=False)}

Model answer:
{question.model_answer or ""}

Student answer from OCR:
{answer_text}

Requirements for rubric_breakdown:
- Include one entry for each supplied rubric item.
- "max" must equal that rubric item's maximum marks.
- "awarded" must be between 0 and "max".
- "covered" must be true when the answer covers that rubric item.
- The sum of all "awarded" values MUST equal "suggested_marks".
- "suggested_marks" MUST be between 0 and the maximum marks.

Return exactly this JSON structure:

{{
  "suggested_marks": 0,
  "max_marks": {question.max_marks},
  "rubric_breakdown": [
    {{
      "item": "rubric item",
      "max": 0,
      "awarded": 0,
      "covered": true
    }}
  ],
  "strengths": [],
  "missing_concepts": [],
  "summary": "",
  "confidence": "low",
  "ocr_concern": false
}}
"""

    # ---------------------------------------------------------
    # Gemini client
    # ---------------------------------------------------------
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={
                "error": {
                    "code": "AI_PROVIDER_ERROR",
                    "message": "GEMINI_API_KEY is not configured"
                }
            }
        )

    model_name = os.getenv(
        "GEMINI_MODEL",
        GEMINI_MODEL
    )

    client = genai.Client(
        api_key=api_key
    )

    last_invalid_error = None
    last_provider_error = None

    # ---------------------------------------------------------
    # Retry once
    # ---------------------------------------------------------
    for attempt in range(2):

        # -----------------------------------------------------
        # Gemini provider call
        # -----------------------------------------------------
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.1
                )
            )

        except Exception as exc:
            last_provider_error = exc

            if attempt == 0:
                time.sleep(3)
                continue

            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail={
                    "error": {
                        "code": "AI_PROVIDER_ERROR",
                        "message": str(last_provider_error)
                    }
                }
            )

        # -----------------------------------------------------
        # Response text
        # -----------------------------------------------------
        raw = (response.text or "").strip()

        if not raw:
            last_invalid_error = ValueError(
                "Empty AI response"
            )

            if attempt == 0:
                time.sleep(1)
                continue

            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "error": {
                        "code": "AI_OUTPUT_INVALID",
                        "message": str(last_invalid_error)
                    }
                }
            )

        # -----------------------------------------------------
        # JSON parsing + validation
        # -----------------------------------------------------
        try:
            result = json.loads(raw)

            validated = _validate_ai_output(
                result,
                question
            )

        except (
            json.JSONDecodeError,
            ValueError,
            TypeError,
            KeyError
        ) as exc:

            last_invalid_error = exc

            if attempt == 0:
                time.sleep(1)
                continue

            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "error": {
                        "code": "AI_OUTPUT_INVALID",
                        "message": str(last_invalid_error)
                    }
                }
            )

        # -----------------------------------------------------
        # Store immutable AI suggestion
        # -----------------------------------------------------
        suggestion = AISuggestion(
            sheet_id=sheet_id,
            question_id=question_id,
            suggested_marks=validated["suggested_marks"],
            response=validated,
            model=model_name,
            prompt_version=PROMPT_VERSION,
            validation_status="VALID",
            requested_by=examiner_id
        )

        db.add(suggestion)
        db.commit()
        db.refresh(suggestion)

        return {
            **validated,
            "suggestion_id": suggestion.id,
            "validation_status": suggestion.validation_status,
            "warnings": []
        }

    # Should never reach here.
    raise HTTPException(
        status_code=status.HTTP_502_BAD_GATEWAY,
        detail={
            "error": {
                "code": "AI_PROVIDER_ERROR",
                "message": "AI request failed"
            }
        }
    )


def get_latest_ai_suggestion(
    db,
    sheet_id: int,
    question_id: int
):
    suggestion = (
        db.query(AISuggestion)
        .filter(
            AISuggestion.sheet_id == sheet_id,
            AISuggestion.question_id == question_id
        )
        .order_by(AISuggestion.id.desc())
        .first()
    )

    if suggestion is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="AI suggestion not found"
        )

    return {
        **suggestion.response,
        "suggestion_id": suggestion.id,
        "validation_status": suggestion.validation_status,
        "warnings": []
    }