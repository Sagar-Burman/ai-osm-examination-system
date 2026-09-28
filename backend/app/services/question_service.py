import json

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.exam import Exam
from app.models.question import Question
from app.schemas.question import QuestionCreate, QuestionResponse


def create_question(
    db: Session,
    exam_id: int,
    question_data: QuestionCreate
) -> QuestionResponse:

    exam = (
        db.query(Exam)
        .filter(Exam.id == exam_id)
        .first()
    )

    if exam is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exam not found"
        )

    if exam.is_locked:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="EXAM_LOCKED"
        )

    existing_question = (
        db.query(Question)
        .filter(
            Question.exam_id == exam_id,
            Question.question_number == question_data.number
        )
        .first()
    )

    if existing_question:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Question number already exists for this exam"
        )

    question = Question(
        exam_id=exam_id,
        question_number=question_data.number,
        question_text=question_data.text,
        max_marks=question_data.max_marks,
        rubric=json.dumps(
            [item.model_dump() for item in question_data.rubric]
        ),
        model_answer=question_data.model_answer,
        is_optional=False
    )

    db.add(question)
    db.commit()
    db.refresh(question)

    return QuestionResponse(
        id=question.id,
        exam_id=question.exam_id,
        number=question.question_number,
        text=question.question_text,
        max_marks=question.max_marks,
        rubric=json.loads(question.rubric),
        model_answer=question.model_answer
    )