from __future__ import annotations

from statistics import mean

from sqlalchemy.orm import Session

from app.analytics.examiner_stats import get_all_examiner_stats
from app.models.assignment import Assignment
from app.models.flag import Flag
from app.models.sheet import Sheet


COMPLETED_SHEET_STATUSES = {
    "SUBMITTED",
    "FLAGGED",
    "IN_MODERATION",
    "MODERATED",
    "APPROVED",
    "RESULT_READY",
}


def _status_value(status) -> str:
    return str(getattr(status, "value", status))


def _sheet_completed(sheet: Sheet) -> bool:
    if sheet.submitted_at is not None:
        return True
    return _status_value(sheet.status) in COMPLETED_SHEET_STATUSES


def _average_evaluation_minutes(
    db: Session,
    exam_id: int,
) -> float | None:
    rows = (
        db.query(Assignment, Sheet)
        .join(Sheet, Sheet.id == Assignment.sheet_id)
        .filter(
            Sheet.exam_id == exam_id,
            Assignment.first_opened_at.isnot(None),
            Assignment.submitted_at.isnot(None),
        )
        .all()
    )

    values = []
    for assignment, _sheet in rows:
        seconds = (
            assignment.submitted_at - assignment.first_opened_at
        ).total_seconds()
        if seconds >= 0:
            values.append(seconds / 60.0)

    return mean(values) if values else None


def get_dashboard_stats(
    db: Session,
    exam_id: int,
) -> dict:
    sheets = (
        db.query(Sheet)
        .filter(Sheet.exam_id == exam_id)
        .all()
    )

    total = len(sheets)
    completed = sum(1 for sheet in sheets if _sheet_completed(sheet))
    pending = total - completed

    flagged_sheet_ids = {
        flag.sheet_id
        for flag in (
            db.query(Flag)
            .filter(
                Flag.sheet_id.in_([sheet.id for sheet in sheets])
                if sheets
                else False,
                Flag.status == "OPEN",
            )
            .all()
        )
    }
    flagged = len(flagged_sheet_ids)

    anomaly_count = (
        db.query(Flag)
        .filter(
            Flag.sheet_id.in_([sheet.id for sheet in sheets])
            if sheets
            else False,
        )
        .count()
    )

    progress_pct = (
        (completed / total) * 100.0
        if total
        else 0.0
    )

    examiner_workload = get_all_examiner_stats(db, exam_id)

    return {
        "total": total,
        "completed": completed,
        "pending": pending,
        "flagged": flagged,
        "progress_pct": progress_pct,
        "avg_eval_minutes": _average_evaluation_minutes(db, exam_id),
        "examiner_workload": examiner_workload,
        "anomalies": anomaly_count,
    }
