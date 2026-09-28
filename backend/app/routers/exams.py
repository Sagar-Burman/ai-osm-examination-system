from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import require_role
from app.db.database import SessionLocal
from app.schemas.exam import ExamCreate, ExamResponse
from app.services.exam_service import create_exam


router = APIRouter(
    prefix="/exams",
    tags=["Exams"]
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/", response_model=ExamResponse)
def create_exam_api(
    exam_data: ExamCreate,
    current_user: dict = Depends(require_role("admin")),
    db: Session = Depends(get_db)
):
    return create_exam(
        db=db,
        exam_data=exam_data,
        created_by=int(current_user["sub"])
    )