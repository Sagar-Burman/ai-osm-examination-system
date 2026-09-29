from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.ai_suggestion import AISuggestion
from app.models.answer_segments import AnswerSegment
from app.models.assignment import Assignment
from app.models.audit import AuditLog
from app.models.flag import Flag
from app.models.mark import Mark
from app.models.moderation import Moderation, ModerationDecision
from app.models.page_text import PageText
from app.models.question import Question
from app.models.sheet import Sheet, SheetStatus
from app.models.sheet_pages import SheetPage
from app.models.user import User


_ALLOWED_DECISIONS = {
    ModerationDecision.APPROVE.value,
    ModerationDecision.OVERRIDE.value,
    ModerationDecision.REQUEST_REVIEW.value,
    ModerationDecision.NOTE.value,
}

_SEVERITY_ORDER = {
    "CRITICAL": 4,
    "HIGH": 3,
    "MEDIUM": 2,
    "LOW": 1,
}


def _require_flag_for_sheet(
    db: Session,
    sheet_id: int,
    flag_id: int,
):
    flag = (
        db.query(Flag)
        .filter(
            Flag.id == flag_id,
            Flag.sheet_id == sheet_id,
        )
        .first()
    )

    if flag is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Flag not found for this sheet",
        )

    return flag


def _sheet_total(db: Session, sheet_id: int) -> float:
    marks = (
        db.query(Mark)
        .filter(Mark.sheet_id == sheet_id)
        .all()
    )
    return float(sum(mark.final_marks for mark in marks))


def _write_audit(
    db: Session,
    *,
    user_id: int,
    role: str,
    action: str,
    entity_type: str,
    entity_id: int,
    old_value: dict | None,
    new_value: dict | None,
    ip: str | None,
):
    db.add(
        AuditLog(
            user_id=user_id,
            role=role,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            old_value=old_value,
            new_value=new_value,
            ip=ip,
            timestamp=datetime.utcnow(),
        )
    )


def get_moderation_queue(db: Session) -> list[dict]:
    rows = (
        db.query(Flag, Sheet)
        .join(Sheet, Flag.sheet_id == Sheet.id)
        .filter(Flag.status == "OPEN")
        .all()
    )

    grouped: dict[int, dict] = {}

    for flag, sheet in rows:
        item = grouped.get(sheet.id)
        if item is None:
            item = {
                "sheet_id": sheet.id,
                "anonymous_code": sheet.anonymous_code,
                "exam_id": sheet.exam_id,
                "status": sheet.status.value,
                "flag_count": 0,
                "highest_severity": flag.severity,
                "latest_flag_at": flag.created_at,
                "flags": [],
            }
            grouped[sheet.id] = item

        item["flag_count"] += 1
        if _SEVERITY_ORDER.get(flag.severity, 0) > _SEVERITY_ORDER.get(
            item["highest_severity"], 0
        ):
            item["highest_severity"] = flag.severity

        if flag.created_at > item["latest_flag_at"]:
            item["latest_flag_at"] = flag.created_at

        item["flags"].append(
            {
                "flag_id": flag.id,
                "question_id": flag.question_id,
                "type": flag.type,
                "severity": flag.severity,
                "reason": flag.reason,
                "metric_value": flag.metric_value,
                "related_sheet_id": flag.related_sheet_id,
                "status": flag.status,
                "created_by": flag.created_by,
                "created_at": flag.created_at,
            }
        )

    result = list(grouped.values())
    result.sort(
        key=lambda item: (
            _SEVERITY_ORDER.get(item["highest_severity"], 0),
            item["latest_flag_at"],
        ),
        reverse=True,
    )

    for item in result:
        item.pop("latest_flag_at", None)

    return result


def get_moderation_context(db: Session, sheet_id: int) -> dict:
    sheet = (
        db.query(Sheet)
        .filter(Sheet.id == sheet_id)
        .first()
    )

    if sheet is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sheet not found",
        )

    flags = (
        db.query(Flag)
        .filter(Flag.sheet_id == sheet_id)
        .order_by(Flag.created_at.desc(), Flag.id.desc())
        .all()
    )

    if not any(flag.status == "OPEN" for flag in flags):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No moderation flag found",
        )

    assignment = (
        db.query(Assignment)
        .filter(Assignment.sheet_id == sheet_id)
        .first()
    )

    examiner = None
    if assignment is not None:
        examiner = (
            db.query(User)
            .filter(User.id == assignment.examiner_id)
            .first()
        )

    pages = (
        db.query(SheetPage)
        .filter(SheetPage.sheet_id == sheet_id)
        .order_by(SheetPage.page_no)
        .all()
    )

    page_texts = (
        db.query(PageText)
        .filter(PageText.sheet_id == sheet_id)
        .order_by(PageText.page_no)
        .all()
    )

    marks = (
        db.query(Mark)
        .filter(Mark.sheet_id == sheet_id)
        .all()
    )
    marks_by_question = {mark.question_id: mark for mark in marks}

    question_ids = {
        flag.question_id
        for flag in flags
        if flag.question_id is not None
    }

    if not question_ids:
        question_ids = set(marks_by_question)

    questions = (
        db.query(Question)
        .filter(Question.id.in_(question_ids))
        .order_by(Question.id)
        .all()
        if question_ids
        else []
    )

    question_contexts = []

    for question in questions:
        mark = marks_by_question.get(question.id)
        ai = (
            db.query(AISuggestion)
            .filter(
                AISuggestion.sheet_id == sheet_id,
                AISuggestion.question_id == question.id,
            )
            .order_by(AISuggestion.created_at.desc(), AISuggestion.id.desc())
            .first()
        )

        segments = (
            db.query(AnswerSegment)
            .filter(
                AnswerSegment.sheet_id == sheet_id,
                AnswerSegment.question_id == question.id,
            )
            .order_by(AnswerSegment.page_no, AnswerSegment.id)
            .all()
        )

        question_contexts.append(
            {
                "question_id": question.id,
                "question_number": question.question_number,
                "question_text": question.question_text,
                "max_marks": question.max_marks,
                "rubric": question.rubric,
                "model_answer": question.model_answer,
                "answer_text": "\n".join(
                    segment.text.strip()
                    for segment in segments
                    if segment.text and segment.text.strip()
                ) or None,
                "ai_suggested_marks": (
                    ai.suggested_marks if ai else None
                ),
                "ai_response": ai.response if ai else None,
                "examiner_final_marks": (
                    mark.final_marks if mark else None
                ),
                "eval_status": mark.eval_status if mark else None,
                "prior_comment": mark.comment if mark else None,
                "examiner_id": mark.examiner_id if mark else (
                    assignment.examiner_id if assignment else None
                ),
            }
        )

    return {
        "sheet_id": sheet.id,
        "anonymous_code": sheet.anonymous_code,
        "exam_id": sheet.exam_id,
        "status": sheet.status.value,
        "examiner": (
            {
                "examiner_id": examiner.id,
                "examiner_username": examiner.username,
            }
            if examiner
            else None
        ),
        "pages": [
            {
                "page_no": page.page_no,
                "image_path": page.image_path,
                "is_cover": page.is_cover,
            }
            for page in pages
        ],
        "ocr_text": [
            {
                "page_no": page.page_no,
                "raw_text": page.raw_text,
                "ocr_confidence": page.ocr_confidence,
                "ocr_status": page.ocr_status,
            }
            for page in page_texts
        ],
        "questions": question_contexts,
        "flags": [
            {
                "flag_id": flag.id,
                "question_id": flag.question_id,
                "type": flag.type,
                "severity": flag.severity,
                "reason": flag.reason,
                "metric_value": flag.metric_value,
                "related_sheet_id": flag.related_sheet_id,
                "status": flag.status,
                "created_by": flag.created_by,
                "created_at": flag.created_at,
            }
            for flag in flags
        ],
        "current_total": _sheet_total(db, sheet_id),
    }


def apply_moderation_decision(
    db: Session,
    *,
    sheet_id: int,
    moderator_id: int,
    moderator_role: str,
    flag_id: int,
    decision: str,
    new_marks: list,
    note: str | None,
    ip: str | None,
) -> dict:
    if decision not in _ALLOWED_DECISIONS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid moderation decision",
        )

    flag = _require_flag_for_sheet(db, sheet_id, flag_id)

    if flag.status == "RESOLVED" and decision != ModerationDecision.NOTE.value:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="FLAG_ALREADY_RESOLVED",
        )

    if decision in {
        ModerationDecision.OVERRIDE.value,
        ModerationDecision.REQUEST_REVIEW.value,
    } and not (note and note.strip()):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="NOTE_REQUIRED",
        )

    sheet = (
        db.query(Sheet)
        .filter(Sheet.id == sheet_id)
        .first()
    )

    if sheet is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sheet not found",
        )

    old_total = _sheet_total(db, sheet_id)
    new_total = old_total
    old_sheet_status = sheet.status.value
    old_flag_status = flag.status

    if decision == ModerationDecision.OVERRIDE.value:
        if not new_marks:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="new_marks is required for OVERRIDE",
            )

        exam_questions = {
            question.id: question
            for question in (
                db.query(Question)
                .filter(Question.exam_id == sheet.exam_id)
                .all()
            )
        }

        marks_by_question = {
            mark.question_id: mark
            for mark in (
                db.query(Mark)
                .filter(Mark.sheet_id == sheet_id)
                .all()
            )
        }

        for item in new_marks:
            question_id = int(item.question_id)
            marks_value = float(item.marks)
            question = exam_questions.get(question_id)

            if question is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Question not found",
                )

            if marks_value < 0 or marks_value > question.max_marks:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Marks outside question maximum",
                )

            mark_step = 0.5
            try:
                exam = None
                # The exam object is only needed for mark_step. Keep lookup local.
                from app.models.exam import Exam
                exam = db.query(Exam).filter(Exam.id == sheet.exam_id).first()
                mark_step = exam.mark_step or 0.5
            except Exception:
                mark_step = 0.5

            quotient = marks_value / mark_step
            if abs(quotient - round(quotient)) > 1e-9:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Marks must be in {mark_step} steps.",
                )

            mark = marks_by_question.get(question_id)
            if mark is None:
                mark = Mark(
                    sheet_id=sheet_id,
                    question_id=question_id,
                    final_marks=marks_value,
                    eval_status="EVALUATED",
                    ai_suggestion_id=None,
                    ai_action="NONE",
                    comment=note,
                    examiner_id=(
                        db.query(Assignment)
                        .filter(Assignment.sheet_id == sheet_id)
                        .first()
                        .examiner_id
                    ),
                    updated_at=datetime.utcnow(),
                )
                db.add(mark)
            else:
                mark.final_marks = marks_value
                mark.eval_status = "EVALUATED"
                mark.comment = note or mark.comment
                mark.updated_at = datetime.utcnow()

        db.flush()
        new_total = _sheet_total(db, sheet_id)
        sheet.total_marks = new_total

    elif decision == ModerationDecision.REQUEST_REVIEW.value:
        sheet.status = SheetStatus.IN_EVALUATION
        flag.status = "RESOLVED"
    elif decision == ModerationDecision.APPROVE.value:
        flag.status = "RESOLVED"
    elif decision == ModerationDecision.NOTE.value:
        # A note is recorded without resolving the open flag.
        pass

    # For APPROVE/OVERRIDE, the selected flag is resolved. Keep the sheet
    # flagged while other open flags remain; otherwise move it to MODERATED.
    if decision in {
        ModerationDecision.APPROVE.value,
        ModerationDecision.OVERRIDE.value,
    }:
        flag.status = "RESOLVED"
        remaining_open_flags = (
            db.query(Flag)
            .filter(
                Flag.sheet_id == sheet_id,
                Flag.status == "OPEN",
                Flag.id != flag.id,
            )
            .count()
        )
        sheet.status = (
            SheetStatus.MODERATED
            if remaining_open_flags == 0
            else SheetStatus.FLAGGED
        )

    moderation = Moderation(
        flag_id=flag.id,
        sheet_id=sheet_id,
        moderator_id=moderator_id,
        decision=decision,
        old_total=old_total,
        new_total=new_total if decision == ModerationDecision.OVERRIDE.value else old_total,
        note=note,
        created_at=datetime.utcnow(),
    )
    db.add(moderation)
    db.flush()

    _write_audit(
        db,
        user_id=moderator_id,
        role=moderator_role,
        action=f"MODERATION_{decision}",
        entity_type="flag",
        entity_id=flag.id,
        old_value={
            "flag_status": old_flag_status,
            "sheet_status": old_sheet_status,
            "total": old_total,
        },
        new_value={
            "decision": decision,
            "flag_status": flag.status,
            "sheet_status": sheet.status.value,
            "total": new_total,
            "note": note,
        },
        ip=ip,
    )

    db.commit()
    db.refresh(moderation)
    db.refresh(flag)
    db.refresh(sheet)

    return {
        "status": "MODERATED" if decision != ModerationDecision.NOTE.value else "NOTE_ADDED",
        "sheet_id": sheet_id,
        "flag_id": flag.id,
        "decision": decision,
        "sheet_status": sheet.status.value,
        "flag_status": flag.status,
        "old_total": old_total,
        "new_total": new_total,
        "moderation_id": moderation.id,
    }
