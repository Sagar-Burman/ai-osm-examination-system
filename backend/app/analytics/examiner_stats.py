from __future__ import annotations

from statistics import mean, pvariance, pstdev

from sqlalchemy.orm import Session

from app.models.assignment import Assignment
from app.models.flag import Flag
from app.models.mark import Mark
from app.models.sheet import Sheet
from app.models.user import User


COMPLETED_SHEET_STATUSES = {
    "SUBMITTED",
    "FLAGGED",
    "IN_MODERATION",
    "MODERATED",
    "APPROVED",
    "RESULT_READY",
}

AI_ACTIONS = {"ACCEPTED", "EDITED", "IGNORED"}


def _is_completed(assignment: Assignment, sheet: Sheet) -> bool:
    if assignment.submitted_at is not None:
        return True

    status = getattr(sheet.status, "value", sheet.status)
    return status in COMPLETED_SHEET_STATUSES


def _evaluation_minutes(assignment: Assignment, sheet: Sheet) -> float | None:
    start = assignment.first_opened_at
    end = assignment.submitted_at or sheet.submitted_at

    if start is None or end is None:
        return None

    seconds = (end - start).total_seconds()
    if seconds < 0:
        return None

    return seconds / 60.0


def get_examiner_stats(
    db: Session,
    examiner_id: int,
    exam_id: int | None = None,
) -> dict:
    examiner = (
        db.query(User)
        .filter(User.id == examiner_id)
        .first()
    )

    if examiner is None:
        raise ValueError("Examiner not found.")

    query = (
        db.query(Assignment, Sheet)
        .join(Sheet, Sheet.id == Assignment.sheet_id)
        .filter(Assignment.examiner_id == examiner_id)
    )

    if exam_id is not None:
        query = query.filter(Sheet.exam_id == exam_id)

    rows = query.all()

    assigned = len(rows)
    completed_rows = [
        (assignment, sheet)
        for assignment, sheet in rows
        if _is_completed(assignment, sheet)
    ]
    completed = len(completed_rows)
    pending = assigned - completed

    evaluation_times = []
    totals = []

    completed_sheet_ids = []

    for assignment, sheet in completed_rows:
        completed_sheet_ids.append(sheet.id)

        minutes = _evaluation_minutes(assignment, sheet)
        if minutes is not None:
            evaluation_times.append(minutes)

        if sheet.total_marks is not None:
            totals.append(float(sheet.total_marks))

    avg_evaluation_time_minutes = (
        mean(evaluation_times)
        if evaluation_times
        else None
    )

    avg_marks = mean(totals) if totals else None
    score_variance = pvariance(totals) if len(totals) >= 2 else None
    score_std = pstdev(totals) if len(totals) >= 2 else None

    flagged_cases = 0
    if completed_sheet_ids:
        flagged_cases = (
            db.query(Flag.sheet_id)
            .filter(Flag.sheet_id.in_(completed_sheet_ids))
            .distinct()
            .count()
        )

    marks_query = db.query(Mark).filter(
        Mark.examiner_id == examiner_id
    )
    if completed_sheet_ids:
        marks_query = marks_query.filter(
            Mark.sheet_id.in_(completed_sheet_ids)
        )
    else:
        marks_query = marks_query.filter(False)

    marks = marks_query.all()

    ai_action_counts = {
        "ACCEPTED": 0,
        "EDITED": 0,
        "IGNORED": 0,
    }

    for mark in marks:
        action = str(mark.ai_action or "NONE").upper()
        if action in AI_ACTIONS:
            ai_action_counts[action] += 1

    ai_action_total = sum(ai_action_counts.values())

    ai_accept_rate_pct = (
        ai_action_counts["ACCEPTED"] / ai_action_total * 100
        if ai_action_total
        else 0.0
    )
    ai_edit_rate_pct = (
        ai_action_counts["EDITED"] / ai_action_total * 100
        if ai_action_total
        else 0.0
    )
    ai_ignore_rate_pct = (
        ai_action_counts["IGNORED"] / ai_action_total * 100
        if ai_action_total
        else 0.0
    )

    return {
        "examiner_id": examiner.id,
        "examiner_username": examiner.username,
        "assigned": assigned,
        "completed": completed,
        "pending": pending,
        "avg_evaluation_time_minutes": avg_evaluation_time_minutes,
        "avg_marks": avg_marks,
        "score_variance": score_variance,
        "score_std": score_std,
        "flagged_cases": flagged_cases,
        "ai_accept_count": ai_action_counts["ACCEPTED"],
        "ai_edit_count": ai_action_counts["EDITED"],
        "ai_ignore_count": ai_action_counts["IGNORED"],
        "ai_accept_rate_pct": ai_accept_rate_pct,
        "ai_edit_rate_pct": ai_edit_rate_pct,
        "ai_ignore_rate_pct": ai_ignore_rate_pct,
    }


def get_all_examiner_stats(
    db: Session,
    exam_id: int,
) -> list[dict]:
    examiners = (
        db.query(User)
        .filter(User.role == "examiner")
        .order_by(User.id)
        .all()
    )

    return [
        get_examiner_stats(db, examiner.id, exam_id)
        for examiner in examiners
    ]
