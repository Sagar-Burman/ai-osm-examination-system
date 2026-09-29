from datetime import datetime, timedelta

from app.db.database import SessionLocal
from app.models.assignment import Assignment
from app.models.flag import Flag
from app.models.mark import Mark
from app.models.question import Question
from app.models.sheet import Sheet, SheetStatus
from app.services.anomaly_service import run_anomaly_checks


EXAM_ID = 1
EXAMINER_ID = 2
ADMIN_ID = 1
PREFIX = "ANOMTEST-"


def main():
    db = SessionLocal()

    try:
        question_ids = [
            q.id
            for q in (
                db.query(Question)
                .filter(Question.exam_id == EXAM_ID)
                .order_by(Question.id)
                .limit(2)
                .all()
            )
        ]

        if len(question_ids) < 2:
            raise RuntimeError(
                "Exam 1 needs at least 2 questions for this test."
            )

        q1_id, q2_id = question_ids

        # Remove only previous synthetic anomaly-test data.
        old_sheets = (
            db.query(Sheet)
            .filter(Sheet.anonymous_code.like(f"{PREFIX}%"))
            .all()
        )

        old_ids = [sheet.id for sheet in old_sheets]

        if old_ids:
            db.query(Flag).filter(Flag.sheet_id.in_(old_ids)).delete(
                synchronize_session=False
            )
            db.query(Mark).filter(Mark.sheet_id.in_(old_ids)).delete(
                synchronize_session=False
            )
            db.query(Assignment).filter(
                Assignment.sheet_id.in_(old_ids)
            ).delete(
                synchronize_session=False
            )
            db.query(Sheet).filter(Sheet.id.in_(old_ids)).delete(
                synchronize_session=False
            )
            db.commit()

        existing = db.query(Sheet).filter(Sheet.id == 5).first()
        if existing is None:
            raise RuntimeError("Existing sheet 5 was not found.")

        now = datetime.utcnow()

        # 9 baseline sheets with total = 5 and 1 outlier with total = 10.
        # Q1 = 0 (confirmed blank), Q2 = 5 for baseline.
        # Outlier Q2 = 10.
        totals = [5.0] * 9 + [10.0]

        created = []

        for i, q2_marks in enumerate(totals, start=1):
            sheet = Sheet(
                exam_id=EXAM_ID,
                anonymous_code=f"{PREFIX}{i:02d}",
                file_path=existing.file_path,
                page_count=existing.page_count,
                cover_page_no=existing.cover_page_no,
                status=SheetStatus.SUBMITTED,
                qc_status=existing.qc_status,
                processing_status=existing.processing_status,
                uploaded_by=ADMIN_ID,
                uploaded_at=now - timedelta(hours=2, minutes=i),
                submitted_at=now - timedelta(minutes=i),
                total_marks=q2_marks,
            )
            db.add(sheet)
            db.flush()

            assignment = Assignment(
                sheet_id=sheet.id,
                examiner_id=EXAMINER_ID,
                assigned_by=ADMIN_ID,
                assigned_at=now - timedelta(hours=2, minutes=i),
                status="SUBMITTED",
                first_opened_at=now - timedelta(minutes=10 + i),
                submitted_at=sheet.submitted_at,
            )
            db.add(assignment)

            db.add(
                Mark(
                    sheet_id=sheet.id,
                    question_id=q1_id,
                    final_marks=0,
                    eval_status="CONFIRMED_BLANK",
                    ai_action="NONE",
                    comment=None,
                    examiner_id=EXAMINER_ID,
                    updated_at=sheet.submitted_at,
                )
            )

            db.add(
                Mark(
                    sheet_id=sheet.id,
                    question_id=q2_id,
                    final_marks=q2_marks,
                    eval_status="EVALUATED",
                    ai_action="NONE",
                    comment=None,
                    examiner_id=EXAMINER_ID,
                    updated_at=sheet.submitted_at,
                )
            )

            created.append(sheet)

        db.commit()

        outlier = created[-1]

        flags = run_anomaly_checks(db, outlier.id)

        print("ANOMALY TEST DATA READY")
        print(f"Created sheets: {len(created)}")
        print(f"Baseline totals: 5 x 9")
        print("Outlier total: 10")
        print(f"Outlier sheet ID: {outlier.id}")
        print(f"Flags created: {len(flags)}")

        for flag in flags:
            print(
                f"- {flag.type}: {flag.reason} "
                f"(metric={flag.metric_value})"
            )

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    main()
