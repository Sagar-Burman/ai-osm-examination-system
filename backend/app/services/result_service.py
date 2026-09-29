from __future__ import annotations

import csv
import io
from datetime import datetime

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.exam import Exam
from app.models.flag import Flag
from app.models.identity import IdentityMap
from app.models.mark import Mark
from app.models.question import Question
from app.models.result import Result
from app.models.sheet import Sheet, SheetStatus
from app.services.audit_service import write_audit


_ELIGIBLE_STATUSES = {SheetStatus.MODERATED}

# Some project versions do not define EVALUATED_OK in the SheetStatus enum.
# When it exists, accept it exactly as documented without breaking older enums.
if hasattr(SheetStatus, "EVALUATED_OK"):
    _ELIGIBLE_STATUSES.add(SheetStatus.EVALUATED_OK)


def _questions_for_sheet(db: Session, sheet: Sheet) -> list[Question]:
    return (
        db.query(Question)
        .filter(Question.exam_id == sheet.exam_id)
        .order_by(Question.id)
        .all()
    )


def _open_flags(db: Session, sheet_id: int) -> list[Flag]:
    return (
        db.query(Flag)
        .filter(Flag.sheet_id == sheet_id, Flag.status == "OPEN")
        .all()
    )


def _validation(
    db: Session,
    sheet: Sheet,
    *,
    allow_approved: bool = False,
) -> tuple[bool, list[str], float, dict]:
    reasons: list[str] = []

    allowed_statuses = set(_ELIGIBLE_STATUSES)
    if allow_approved:
        allowed_statuses.add(SheetStatus.APPROVED)

    if sheet.status not in allowed_statuses:
        reasons.append(f"SHEET_NOT_READY:{sheet.status.value}")

    if _open_flags(db, sheet.id):
        reasons.append("OPEN_FLAGS_EXIST")

    questions = _questions_for_sheet(db, sheet)
    marks = db.query(Mark).filter(Mark.sheet_id == sheet.id).all()
    marks_by_question = {mark.question_id: mark for mark in marks}

    question_marks: dict[str, float] = {}
    total = 0.0

    for question in questions:
        mark = marks_by_question.get(question.id)
        if mark is None or mark.eval_status not in {"EVALUATED", "CONFIRMED_BLANK"}:
            reasons.append("NOT_ALL_EVALUATED")
            continue

        value = float(mark.final_marks)
        if value < 0 or value > float(question.max_marks):
            reasons.append("INVALID_MARKS")
            continue

        total += value
        question_marks[str(question.number if hasattr(question, "number") else question.question_number)] = value

    if len(question_marks) != len(questions):
        if "NOT_ALL_EVALUATED" not in reasons:
            reasons.append("NOT_ALL_EVALUATED")

    exam = db.query(Exam).filter(Exam.id == sheet.exam_id).first()
    if exam is None:
        reasons.append("EXAM_NOT_FOUND")
    elif total > float(exam.total_marks):
        reasons.append("TOTAL_EXCEEDS_EXAM")

    reasons = list(dict.fromkeys(reasons))
    return len(reasons) == 0, reasons, total, question_marks


def get_readiness(db: Session, exam_id: int) -> dict:
    sheets = (
        db.query(Sheet)
        .filter(Sheet.exam_id == exam_id)
        .order_by(Sheet.id)
        .all()
    )
    ready = []
    blocked = []

    for sheet in sheets:
        ok, reasons, total, _ = _validation(db, sheet)
        item = {
            "sheet_id": sheet.id,
            "anonymous_code": sheet.anonymous_code,
            "status": sheet.status.value,
            "total_marks": total,
        }
        if ok:
            ready.append(item)
        else:
            item["reasons"] = reasons
            blocked.append(item)

    return {
        "exam_id": exam_id,
        "ready_count": len(ready),
        "blocked_count": len(blocked),
        "ready_sheets": ready,
        "blocked_sheets": blocked,
    }


def _get_ready_sheet(db: Session, sheet_id: int) -> tuple[Sheet, float, dict]:
    sheet = db.query(Sheet).filter(Sheet.id == sheet_id).first()
    if sheet is None:
        raise HTTPException(status_code=404, detail="Sheet not found")

    ok, reasons, total, question_marks = _validation(db, sheet)
    if not ok:
        if "OPEN_FLAGS_EXIST" in reasons:
            raise HTTPException(status_code=409, detail="OPEN_FLAGS_EXIST")
        if "NOT_ALL_EVALUATED" in reasons:
            raise HTTPException(status_code=409, detail="NOT_ALL_EVALUATED")
        raise HTTPException(
            status_code=409,
            detail={"code": "SHEET_NOT_READY", "reasons": reasons},
        )

    return sheet, total, question_marks


def approve_results(
    db: Session,
    *,
    sheet_ids: list[int],
    admin_id: int,
    role: str,
    ip: str | None,
) -> dict:
    approved: list[int] = []

    for sheet_id in sheet_ids:
        sheet, total, _ = _get_ready_sheet(db, sheet_id)

        old_status = sheet.status.value
        sheet.status = SheetStatus.APPROVED
        sheet.total_marks = total

        write_audit(
            db,
            user_id=admin_id,
            role=role,
            action="RESULT_APPROVED",
            entity_type="sheet",
            entity_id=sheet.id,
            old_value={"status": old_status, "total": total},
            new_value={"status": sheet.status.value, "total": total},
            ip=ip,
        )
        approved.append(sheet.id)

    db.commit()

    return {
        "status": "APPROVED",
        "sheet_ids": approved,
    }


def release_results(
    db: Session,
    *,
    sheet_ids: list[int],
    admin_id: int,
    role: str,
    ip: str | None,
) -> dict:
    released: list[dict] = []

    for sheet_id in sheet_ids:
        sheet = db.query(Sheet).filter(Sheet.id == sheet_id).first()
        if sheet is None:
            raise HTTPException(status_code=404, detail="Sheet not found")
        if sheet.status != SheetStatus.APPROVED:
            raise HTTPException(status_code=409, detail="SHEET_NOT_APPROVED")

        existing = db.query(Result).filter(Result.sheet_id == sheet.id).first()
        if existing is not None:
            raise HTTPException(status_code=409, detail="RESULT_ALREADY_RELEASED")

        # Stage 25 permits identity-map access only here, during admin release.
        identity = (
            db.query(IdentityMap)
            .filter(IdentityMap.sheet_id == sheet.id)
            .first()
        )
        if identity is None:
            raise HTTPException(status_code=409, detail="IDENTITY_MAPPING_NOT_FOUND")

        # Revalidate result data after approval. APPROVED is intentionally
        # accepted here, because the approval step changed the sheet status.
        ok, reasons, total, question_marks = _validation(
            db,
            sheet,
            allow_approved=True,
        )
        if not ok:
            if "OPEN_FLAGS_EXIST" in reasons:
                raise HTTPException(status_code=409, detail="OPEN_FLAGS_EXIST")
            if "NOT_ALL_EVALUATED" in reasons:
                raise HTTPException(status_code=409, detail="NOT_ALL_EVALUATED")
            raise HTTPException(
                status_code=409,
                detail={"code": "SHEET_NOT_READY", "reasons": reasons},
            )

        # The identity-map read itself is audited as required by Stage 24/25.
        write_audit(
            db,
            user_id=admin_id,
            role=role,
            action="IDENTITY_MAPPING_VIEWED",
            entity_type="identity_map",
            entity_id=identity.id,
            old_value=None,
            new_value={"sheet_id": sheet.id, "anonymous_code": sheet.anonymous_code},
            ip=ip,
        )

        now = datetime.utcnow()
        result = Result(
            exam_id=sheet.exam_id,
            sheet_id=sheet.id,
            roll_no=identity.roll_no,
            total_marks=total,
            question_marks=question_marks,
            approved_by=admin_id,
            approved_at=now,
            released_at=now,
        )
        db.add(result)

        old_status = sheet.status.value
        sheet.status = SheetStatus.RESULT_READY
        sheet.total_marks = total

        write_audit(
            db,
            user_id=admin_id,
            role=role,
            action="RESULT_RELEASED",
            entity_type="sheet",
            entity_id=sheet.id,
            old_value={"status": old_status, "anonymous_code": sheet.anonymous_code},
            new_value={"status": sheet.status.value, "total": total},
            ip=ip,
        )

        released.append(
            {
                "sheet_id": sheet.id,
                "roll_no": identity.roll_no,
                "total_marks": total,
                "status": sheet.status.value,
            }
        )

    db.commit()
    return {"status": "RESULT_READY", "results": released}


def export_results(db: Session, *, exam_id: int) -> str:
    rows = (
        db.query(Result)
        .filter(Result.exam_id == exam_id)
        .order_by(Result.sheet_id)
        .all()
    )

    question_numbers: list[str] = []
    for row in rows:
        for key in (row.question_marks or {}).keys():
            if key not in question_numbers:
                question_numbers.append(key)

    output = io.StringIO(newline="")
    fieldnames = ["roll_no", "total_marks"] + [f"Q{number}" for number in question_numbers]
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()

    for row in rows:
        data = {"roll_no": row.roll_no, "total_marks": row.total_marks}
        for number in question_numbers:
            data[f"Q{number}"] = (row.question_marks or {}).get(number, "")
        writer.writerow(data)

    return output.getvalue()
