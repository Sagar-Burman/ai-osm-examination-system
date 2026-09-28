from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.deps import require_role
from app.db.database import SessionLocal
from app.schemas.question import QuestionCreate, QuestionResponse
from app.services.question_service import create_question


router = APIRouter(
    prefix="/exams",
    tags=["Questions"]
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post(
    "/{exam_id}/questions",
    response_model=QuestionResponse,
    status_code=status.HTTP_201_CREATED
)
def create_question_api(
    exam_id: int,
    question_data: QuestionCreate,
    current_user: dict = Depends(require_role("admin")),
    db: Session = Depends(get_db)
):
    return create_question(
        db=db,
        exam_id=exam_id,
        question_data=question_data
    )