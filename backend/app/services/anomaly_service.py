from __future__ import annotations

from datetime import datetime
from statistics import median

from sqlalchemy.orm import Session

from app.ml.anomaly import z_score
from app.ml.similarity import find_similar_pairs
from app.models.assignment import Assignment
from app.models.answer_segments import AnswerSegment
from app.models.flag import Flag
from app.models.mark import Mark
from app.models.question import Question
from app.models.sheet import Sheet, SheetStatus


def _submitted_examiner_sheets(db: Session, examiner_id: int, exam_id: int):
    return (
        db.query(Sheet)
        .join(Assignment, Assignment.sheet_id == Sheet.id)
        .filter(
            Assignment.examiner_id == examiner_id,
            Sheet.exam_id == exam_id,
            Sheet.status.in_([
                SheetStatus.SUBMITTED,
                SheetStatus.FLAGGED,
            ]),
        )
        .all()
    )


def _submitted_exam_sheets(db: Session, exam_id: int):
    return (
        db.query(Sheet)
        .filter(
            Sheet.exam_id == exam_id,
            Sheet.status.in_([
                SheetStatus.SUBMITTED,
                SheetStatus.FLAGGED,
            ]),
        )
        .all()
    )


def _sheet_total(db: Session, sheet_id: int) -> float:
    marks = db.query(Mark).filter(Mark.sheet_id == sheet_id).all()
    return float(sum(mark.final_marks for mark in marks))


def _add_flag(
    db: Session,
    *,
    sheet_id: int,
    flag_type: str,
    reason: str,
    metric_value: float | None = None,
    question_id: int | None = None,
):
    existing = (
        db.query(Flag)
        .filter(
            Flag.sheet_id == sheet_id,
            Flag.type == flag_type,
            Flag.question_id == question_id,
            Flag.reason == reason,
            Flag.status == "OPEN",
        )
        .first()
    )

    if existing:
        return existing

    flag = Flag(
        sheet_id=sheet_id,
        question_id=question_id,
        type=flag_type,
        severity="MEDIUM",
        reason=reason,
        metric_value=metric_value,
        related_sheet_id=None,
        status="OPEN",
        created_by="SYSTEM",
        created_at=datetime.utcnow(),
    )
    db.add(flag)
    return flag



def _run_similarity_checks(
    db: Session,
    sheet_id: int,
) -> list[Flag]:
    """Stage 20: compare OCR answer text for the same question across sheets."""
    sheet = db.query(Sheet).filter(Sheet.id == sheet_id).first()
    if sheet is None:
        return []

    exam_sheet_ids = [
        item.id
        for item in _submitted_exam_sheets(db, sheet.exam_id)
    ]

    if sheet_id not in exam_sheet_ids:
        exam_sheet_ids.append(sheet_id)

    segments = (
        db.query(AnswerSegment)
        .filter(
            AnswerSegment.sheet_id.in_(exam_sheet_ids)
        )
        .all()
    )

    # Combine multiple OCR segments belonging to the same sheet/question.
    combined: dict[int, dict[int, list[str]]] = {}

    for segment in segments:
        text = (segment.text or "").strip()
        if not text:
            continue

        combined.setdefault(
            int(segment.question_id),
            {}
        ).setdefault(
            int(segment.sheet_id),
            []
        ).append(text)

    created_flags: list[Flag] = []

    for question_id, sheet_texts in combined.items():
        texts = [
            (sid, " ".join(parts))
            for sid, parts in sheet_texts.items()
        ]

        pairs = find_similar_pairs(texts)

        for pair in pairs:
            if (
                pair["sheet_id"] != sheet_id
                and pair["related_sheet_id"] != sheet_id
            ):
                continue

            other_sheet_id = (
                pair["related_sheet_id"]
                if pair["sheet_id"] == sheet_id
                else pair["sheet_id"]
            )

            reason = (
                f"Potentially high textual similarity "
                f"({pair['similarity']:.2f}) — review recommended."
            )

            existing = (
                db.query(Flag)
                .filter(
                    Flag.sheet_id == sheet_id,
                    Flag.question_id == question_id,
                    Flag.type == "SIMILARITY",
                    Flag.related_sheet_id == other_sheet_id,
                    Flag.reason == reason,
                    Flag.status == "OPEN",
                )
                .first()
            )

            if existing:
                continue

            flag = Flag(
                sheet_id=sheet_id,
                question_id=question_id,
                type="SIMILARITY",
                severity="MEDIUM",
                reason=reason,
                metric_value=pair["similarity"],
                related_sheet_id=other_sheet_id,
                status="OPEN",
                created_by="SYSTEM",
                created_at=datetime.utcnow(),
            )
            db.add(flag)
            created_flags.append(flag)

    if created_flags:
        sheet.status = SheetStatus.FLAGGED
        db.commit()

        for flag in created_flags:
            db.refresh(flag)

    return created_flags


def run_anomaly_checks(
    db: Session,
    sheet_id: int,
) -> list[Flag]:
    sheet = db.query(Sheet).filter(Sheet.id == sheet_id).first()
    if sheet is None:
        return []

    assignment = (
        db.query(Assignment)
        .filter(Assignment.sheet_id == sheet_id)
        .first()
    )
    if assignment is None:
        return []

    created_flags: list[Flag] = []
    current_total = _sheet_total(db, sheet_id)

    # 1. Total vs examiner's other sheets: |z| > 2.5, minimum 5 sheets.
    examiner_sheets = _submitted_examiner_sheets(
        db,
        assignment.examiner_id,
        sheet.exam_id,
    )
    if len(examiner_sheets) >= 5:
        examiner_totals = [
            _sheet_total(db, item.id)
            for item in examiner_sheets
            if item.id != sheet_id
        ]
        if len(examiner_totals) >= 4:
            score = z_score(current_total, examiner_totals)
            if score is not None and abs(score) > 2.5:
                created_flags.append(
                    _add_flag(
                        db,
                        sheet_id=sheet_id,
                        flag_type="MARKS_OUTLIER",
                        reason=(
                            "Unusual pattern detected: total marks far from "
                            "this examiner's average. Review recommended."
                        ),
                        metric_value=score,
                    )
                )

    # 2. Total vs all sheets in the exam: |z| > 3.
    exam_sheets = _submitted_exam_sheets(db, sheet.exam_id)
    exam_totals = [
        _sheet_total(db, item.id)
        for item in exam_sheets
        if item.id != sheet_id
    ]
    if len(exam_totals) >= 2:
        score = z_score(current_total, exam_totals)
        if score is not None and abs(score) > 3:
            created_flags.append(
                _add_flag(
                    db,
                    sheet_id=sheet_id,
                    flag_type="MARKS_OUTLIER",
                    reason="Potential anomaly: score unusual for this exam.",
                    metric_value=score,
                )
            )

    # 3. Evaluation time vs median: <20% or >5x median.
    current_assignment = assignment
    current_time = None
    if current_assignment.first_opened_at and sheet.submitted_at:
        current_time = (
            sheet.submitted_at - current_assignment.first_opened_at
        ).total_seconds()

    times = []
    for item in exam_sheets:
        if item.id == sheet_id:
            continue
        item_assignment = (
            db.query(Assignment)
            .filter(Assignment.sheet_id == item.id)
            .first()
        )
        if item_assignment and item_assignment.first_opened_at and item.submitted_at:
            times.append(
                (
                    item.submitted_at - item_assignment.first_opened_at
                ).total_seconds()
            )

    if current_time is not None and times:
        baseline = median(times)
        if baseline > 0 and (
            current_time < 0.2 * baseline
            or current_time > 5 * baseline
        ):
            created_flags.append(
                _add_flag(
                    db,
                    sheet_id=sheet_id,
                    flag_type="TIME_ANOMALY",
                    reason="Potential anomaly: very fast/slow evaluation.",
                    metric_value=current_time / baseline,
                )
            )

    # 4. Question-level pattern vs exam: |z| > 2.5.
    questions = (
        db.query(Question)
        .filter(Question.exam_id == sheet.exam_id)
        .all()
    )

    for question in questions:
        current_mark = (
            db.query(Mark)
            .filter(
                Mark.sheet_id == sheet_id,
                Mark.question_id == question.id,
            )
            .first()
        )
        if current_mark is None:
            continue

        other_marks = [
            float(mark.final_marks)
            for other_sheet in exam_sheets
            if other_sheet.id != sheet_id
            for mark in db.query(Mark).filter(
                Mark.sheet_id == other_sheet.id,
                Mark.question_id == question.id,
            ).all()
        ]

        if len(other_marks) < 2:
            continue

        score = z_score(float(current_mark.final_marks), other_marks)
        if score is not None and abs(score) > 2.5:
            created_flags.append(
                _add_flag(
                    db,
                    sheet_id=sheet_id,
                    question_id=question.id,
                    flag_type="QUESTION_PATTERN",
                    reason=f"Unusual pattern on Q{question.question_number}.",
                    metric_value=score,
                )
            )

    similarity_flags = _run_similarity_checks(db, sheet_id)
    created_flags.extend(similarity_flags)

    if created_flags:
        sheet.status = SheetStatus.FLAGGED
        db.commit()
        for flag in created_flags:
            db.refresh(flag)

    return created_flags
