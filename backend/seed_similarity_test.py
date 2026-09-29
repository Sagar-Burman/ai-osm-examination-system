from sqlalchemy.orm import Session

from app.db.database import SessionLocal
from app.models.answer_segments import AnswerSegment, SegmentSource
from app.models.question import Question
from app.models.sheet import Sheet
from app.services.anomaly_service import run_anomaly_checks


PREFIX = "ANOMTEST-"


SIMILAR_ANSWER = """
Machine learning is a field of artificial intelligence that enables
computers to learn patterns from data and make predictions or decisions
without being explicitly programmed for every task. It uses training data,
features, algorithms, and statistical methods to identify useful patterns.
Machine learning can be divided into supervised learning, unsupervised
learning, and reinforcement learning. Supervised learning uses labelled data
for classification and regression. Unsupervised learning finds hidden
patterns or groups in unlabelled data. Reinforcement learning learns through
actions, rewards, and feedback from an environment. Common applications
include recommendation systems, fraud detection, image recognition, speech
recognition, medical analysis, and demand prediction. Machine learning
systems improve when they receive suitable training data and appropriate
features, and their performance is evaluated using relevant metrics.
"""


def main():
    db: Session = SessionLocal()

    try:
        # Find the synthetic sheets created by Stage 19 test.
        sheets = (
            db.query(Sheet)
            .filter(Sheet.anonymous_code.like(f"{PREFIX}%"))
            .order_by(Sheet.id)
            .all()
        )

        if len(sheets) < 2:
            raise RuntimeError(
                "Need at least 2 ANOMTEST sheets. "
                "Run seed_anomaly_test.py first."
            )

        first_sheet = sheets[0]
        second_sheet = sheets[1]

        # Both sheets must belong to the same exam.
        if first_sheet.exam_id != second_sheet.exam_id:
            raise RuntimeError(
                "The first two test sheets are not from the same exam."
            )

        # Stage 20 compares the SAME question.
        question = (
            db.query(Question)
            .filter(
                Question.exam_id == first_sheet.exam_id,
                Question.question_number == "2",
            )
            .first()
        )

        if question is None:
            question = (
                db.query(Question)
                .filter(Question.exam_id == first_sheet.exam_id)
                .order_by(Question.id)
                .first()
            )

        if question is None:
            raise RuntimeError(
                "No question found for the test exam."
            )

        # Remove previous test segments for this question.
        db.query(AnswerSegment).filter(
            AnswerSegment.sheet_id.in_(
                [first_sheet.id, second_sheet.id]
            ),
            AnswerSegment.question_id == question.id,
        ).delete(synchronize_session=False)

        # Create identical long OCR answer text on both sheets.
        first_segment = AnswerSegment(
            sheet_id=first_sheet.id,
            question_id=question.id,
            page_no=2,
            region=None,
            text=SIMILAR_ANSWER.strip(),
            is_blank_detected=False,
            source=SegmentSource.AUTO,
        )

        second_segment = AnswerSegment(
            sheet_id=second_sheet.id,
            question_id=question.id,
            page_no=2,
            region=None,
            text=SIMILAR_ANSWER.strip(),
            is_blank_detected=False,
            source=SegmentSource.AUTO,
        )

        db.add(first_segment)
        db.add(second_segment)
        db.commit()

        # Run anomaly + similarity checks on the second sheet.
        flags = run_anomaly_checks(
            db,
            second_sheet.id,
        )

        similarity_flags = [
            flag
            for flag in flags
            if flag.type == "SIMILARITY"
        ]

        print("SIMILARITY TEST READY")
        print(f"Sheet 1 ID: {first_sheet.id}")
        print(f"Sheet 2 ID: {second_sheet.id}")
        print(f"Question ID: {question.id}")
        print(f"Question Number: {question.question_number}")
        print(f"Similarity flags created: {len(similarity_flags)}")

        for flag in similarity_flags:
            print(
                f"- {flag.type}: {flag.reason} "
                f"(metric={flag.metric_value}, "
                f"related_sheet_id={flag.related_sheet_id})"
            )

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    main()