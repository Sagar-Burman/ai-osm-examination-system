from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.assignment import Assignment
from app.models.exam import Exam
from app.models.mark import Mark
from app.models.question import Question
from app.models.sheet import Sheet, SheetStatus


def _get_assigned_sheet(
    db: Session,
    sheet_id: int,
    examiner_id: int
):
    result = (
        db.query(Sheet, Assignment, Exam)
        .join(
            Assignment,
            Assignment.sheet_id == Sheet.id
        )
        .join(
            Exam,
            Exam.id == Sheet.exam_id
        )
        .filter(
            Sheet.id == sheet_id,
            Assignment.examiner_id == examiner_id
        )
        .first()
    )

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sheet is not assigned to examiner"
        )

    return result


def open_sheet_for_evaluation(
    db: Session,
    sheet_id: int,
    examiner_id: int
):
    sheet, assignment, exam = _get_assigned_sheet(
        db,
        sheet_id,
        examiner_id
    )

    if sheet.status == SheetStatus.ALLOCATED:
        sheet.status = SheetStatus.IN_EVALUATION

        if assignment.first_opened_at is None:
            assignment.first_opened_at = datetime.utcnow()

        assignment.status = "IN_EVALUATION"

        db.commit()
        db.refresh(sheet)

    elif sheet.status != SheetStatus.IN_EVALUATION:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="SHEET_LOCKED"
        )

    return sheet, assignment, exam


def get_marks(
    db: Session,
    sheet_id: int,
    examiner_id: int,
    allow_moderator: bool = False
):
    if allow_moderator:
        result = (
            db.query(Sheet, Exam)
            .join(Exam, Exam.id == Sheet.exam_id)
            .filter(Sheet.id == sheet_id)
            .first()
        )

        if result is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Sheet not found"
            )

        sheet, exam = result
    else:
        sheet, _, exam = open_sheet_for_evaluation(
            db,
            sheet_id,
            examiner_id
        )

    questions = (
        db.query(Question)
        .filter(Question.exam_id == exam.id)
        .order_by(Question.id)
        .all()
    )

    existing_marks = {
        mark.question_id: mark
        for mark in (
            db.query(Mark)
            .filter(Mark.sheet_id == sheet_id)
            .all()
        )
    }

    question_data = []

    for question in questions:
        mark = existing_marks.get(question.id)

        question_data.append({
            "question_id": question.id,
            "question_number": question.question_number,
            "max_marks": question.max_marks,
            "final_marks": (
                mark.final_marks
                if mark is not None
                else None
            ),
            "eval_status": (
                mark.eval_status
                if mark is not None
                else None
            ),
            "comment": (
                mark.comment
                if mark is not None
                else None
            )
        })

    total = sum(
        mark.final_marks
        for mark in existing_marks.values()
    )

    return {
        "sheet_id": sheet_id,
        "questions": question_data,
        "sheet_total": total
    }


def save_mark(
    db: Session,
    sheet_id: int,
    question_id: int,
    final_marks: float,
    comment: str | None,
    ai_suggestion_id: int | None,
    ai_action: str,
    examiner_id: int
):
    sheet, assignment, exam = open_sheet_for_evaluation(
        db,
        sheet_id,
        examiner_id
    )

    question = (
        db.query(Question)
        .filter(
            Question.id == question_id,
            Question.exam_id == exam.id
        )
        .first()
    )

    if question is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Question not found"
        )

    if final_marks < 0:
        raise HTTPException(
            status_code=422,
            detail="Marks cannot be negative."
        )

    if final_marks > question.max_marks:
        raise HTTPException(
            status_code=422,
            detail=f"Marks cannot exceed {question.max_marks}."
        )

    mark_step = exam.mark_step or 0.5

    quotient = final_marks / mark_step
    if abs(quotient - round(quotient)) > 1e-9:
        raise HTTPException(
            status_code=422,
            detail=f"Marks must be in {mark_step} steps."
        )

    allowed_actions = {
        "ACCEPTED",
        "EDITED",
        "IGNORED",
        "NONE"
    }

    if ai_action not in allowed_actions:
        raise HTTPException(
            status_code=422,
            detail="Invalid AI action"
        )

    mark = (
        db.query(Mark)
        .filter(
            Mark.sheet_id == sheet_id,
            Mark.question_id == question_id
        )
        .first()
    )

    if mark is None:
        mark = Mark(
            sheet_id=sheet_id,
            question_id=question_id,
            final_marks=final_marks,
            eval_status="EVALUATED",
            ai_suggestion_id=ai_suggestion_id,
            ai_action=ai_action,
            comment=comment,
            examiner_id=examiner_id,
            updated_at=datetime.utcnow()
        )
        db.add(mark)
    else:
        mark.final_marks = final_marks
        mark.eval_status = "EVALUATED"
        mark.ai_suggestion_id = ai_suggestion_id
        mark.ai_action = ai_action
        mark.comment = comment
        mark.examiner_id = examiner_id
        mark.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(mark)

    total = sum(
        value.final_marks
        for value in (
            db.query(Mark)
            .filter(Mark.sheet_id == sheet_id)
            .all()
        )
    )

    assignment.status = "IN_EVALUATION"
    db.commit()

    return {
        "question_id": question_id,
        "final_marks": mark.final_marks,
        "eval_status": mark.eval_status,
        "sheet_total": total
    }


def confirm_blank(
    db: Session,
    sheet_id: int,
    question_id: int,
    examiner_id: int
):
    sheet, assignment, exam = open_sheet_for_evaluation(
        db,
        sheet_id,
        examiner_id
    )

    question = (
        db.query(Question)
        .filter(
            Question.id == question_id,
            Question.exam_id == exam.id
        )
        .first()
    )

    if question is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Question not found"
        )

    mark = (
        db.query(Mark)
        .filter(
            Mark.sheet_id == sheet_id,
            Mark.question_id == question_id
        )
        .first()
    )

    if mark is None:
        mark = Mark(
            sheet_id=sheet_id,
            question_id=question_id,
            final_marks=0,
            eval_status="CONFIRMED_BLANK",
            ai_action="NONE",
            comment=None,
            examiner_id=examiner_id,
            updated_at=datetime.utcnow()
        )
        db.add(mark)
    else:
        mark.final_marks = 0
        mark.eval_status = "CONFIRMED_BLANK"
        mark.updated_at = datetime.utcnow()
        mark.examiner_id = examiner_id

    db.commit()
    db.refresh(mark)

    total = sum(
        value.final_marks
        for value in (
            db.query(Mark)
            .filter(Mark.sheet_id == sheet_id)
            .all()
        )
    )

    return {
        "question_id": question_id,
        "final_marks": 0,
        "eval_status": "CONFIRMED_BLANK",
        "sheet_total": total
    }