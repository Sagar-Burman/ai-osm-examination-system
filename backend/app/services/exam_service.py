from sqlalchemy.orm import Session

from app.models.exam import Exam
from app.schemas.exam import ExamCreate


def create_exam(
    db: Session,
    exam_data: ExamCreate,
    created_by: int
) -> Exam:
    exam = Exam(
        name=exam_data.name,
        subject=exam_data.subject,
        exam_date=exam_data.exam_date,
        total_marks=exam_data.total_marks,
        expected_pages=exam_data.expected_pages,
        mark_step=exam_data.mark_step,
        is_locked=False,
        created_by=created_by
    )

    db.add(exam)
    db.commit()
    db.refresh(exam)

    return exam