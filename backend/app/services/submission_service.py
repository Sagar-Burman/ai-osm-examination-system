from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.assignment import Assignment
from app.models.answer_segments import AnswerSegment
from app.models.exam import Exam
from app.models.flag import Flag
from app.models.mark import Mark
from app.models.question import Question
from app.models.sheet import Sheet, SheetStatus
from app.services.anomaly_service import run_anomaly_checks


VALID_EVAL_STATUSES = {
    "EVALUATED",
    "CONFIRMED_BLANK",
}


def _get_assigned_sheet(db: Session, sheet_id: int, examiner_id: int):
    result = (
        db.query(Sheet, Assignment, Exam)
        .join(Assignment, Assignment.sheet_id == Sheet.id)
        .join(Exam, Exam.id == Sheet.exam_id)
        .filter(Sheet.id == sheet_id, Assignment.examiner_id == examiner_id)
        .first()
    )

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sheet is not assigned to examiner",
        )

    return result


def get_question_states(db: Session, sheet_id: int, examiner_id: int):
    sheet, assignment, exam = _get_assigned_sheet(db, sheet_id, examiner_id)

    if sheet.status not in {SheetStatus.ALLOCATED, SheetStatus.IN_EVALUATION}:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="SHEET_LOCKED",
        )

    questions = (
        db.query(Question)
        .filter(Question.exam_id == exam.id)
        .order_by(Question.id)
        .all()
    )

    marks = db.query(Mark).filter(Mark.sheet_id == sheet_id).all()
    marks_by_question = {mark.question_id: mark for mark in marks}

    segments = db.query(AnswerSegment).filter(AnswerSegment.sheet_id == sheet_id).all()
    segments_by_question = {}
    for segment in segments:
        segments_by_question.setdefault(segment.question_id, []).append(segment)

    states = []
    for question in questions:
        mark = marks_by_question.get(question.id)

        if mark is not None:
            state = "CONFIRMED_BLANK" if mark.eval_status == "CONFIRMED_BLANK" else "EVALUATED"
        else:
            question_segments = segments_by_question.get(question.id, [])
            answer_detected = any(
                not segment.is_blank_detected and bool((segment.text or "").strip())
                for segment in question_segments
            )
            state = "ANSWER_DETECTED_UNEVALUATED" if answer_detected else "NOT_ANSWERED"

        states.append({
            "question_id": question.id,
            "question_number": question.question_number,
            "state": state,
        })

    return sheet, assignment, exam, states


def check_submission(db: Session, sheet_id: int, examiner_id: int):
    sheet, assignment, exam, states = get_question_states(db, sheet_id, examiner_id)

    unchecked = [item for item in states if item["state"] not in VALID_EVAL_STATUSES]
    marks = db.query(Mark).filter(Mark.sheet_id == sheet_id).all()
    total = sum(mark.final_marks for mark in marks)

    return {
        "sheet_id": sheet_id,
        "ready": len(unchecked) == 0,
        "questions": states,
        "unchecked_questions": [item["question_number"] for item in unchecked],
        "total_marks": total,
        "status": sheet.status.value,
    }


def submit_sheet(db: Session, sheet_id: int, examiner_id: int):
    sheet, assignment, exam, states = get_question_states(db, sheet_id, examiner_id)

    unchecked = [item for item in states if item["state"] not in VALID_EVAL_STATUSES]
    if unchecked:
        first_question = unchecked[0]["question_number"]
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": {
                    "code": "UNCHECKED_QUESTION",
                    "message": (
                        "Potential unchecked question detected. "
                        f"Please review Q{first_question}."
                    ),
                    "questions": [item["question_number"] for item in unchecked],
                }
            },
        )

    marks = db.query(Mark).filter(Mark.sheet_id == sheet_id).all()
    total = 0.0

    for mark in marks:
        question = (
            db.query(Question)
            .filter(Question.id == mark.question_id, Question.exam_id == exam.id)
            .first()
        )
        if question is None:
            raise HTTPException(status_code=422, detail="INCOMPLETE_MARKING")
        if mark.final_marks < 0:
            raise HTTPException(status_code=422, detail="Marks cannot be negative.")
        if mark.final_marks > question.max_marks:
            raise HTTPException(
                status_code=422,
                detail=f"Marks cannot exceed {question.max_marks}.",
            )

        mark_step = exam.mark_step or 0.5
        quotient = mark.final_marks / mark_step
        if abs(quotient - round(quotient)) > 1e-9:
            raise HTTPException(
                status_code=422,
                detail=f"Marks must be in {mark_step} steps.",
            )
        total += mark.final_marks

    sheet.total_marks = total
    sheet.submitted_at = datetime.utcnow()
    sheet.status = SheetStatus.SUBMITTED
    assignment.status = "SUBMITTED"
    assignment.submitted_at = datetime.utcnow()

    db.commit()
    db.refresh(sheet)

    # Anomaly/similarity checks run after successful submission.
    # If no open flag is created, complete the documented lifecycle:
    # SUBMITTED -> EVALUATED_OK. A flagged sheet remains FLAGGED.
    run_anomaly_checks(db, sheet_id)
    db.refresh(sheet)

    if sheet.status == SheetStatus.SUBMITTED:
        open_flag_exists = (
            db.query(Flag)
            .filter(Flag.sheet_id == sheet_id, Flag.status == "OPEN")
            .first()
            is not None
        )
        if not open_flag_exists:
            sheet.status = SheetStatus.EVALUATED_OK
            db.commit()
            db.refresh(sheet)

    return {
        "status": sheet.status.value,
        "total_marks": total,
    }
