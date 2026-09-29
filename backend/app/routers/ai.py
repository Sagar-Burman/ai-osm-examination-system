from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import require_roles
from app.db.database import SessionLocal
from app.services.ai_eval_service import (
    generate_ai_suggestion,
    get_latest_ai_suggestion
)


router = APIRouter(
    prefix="/sheets",
    tags=["AI Suggestion"]
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/{sheet_id}/questions/{question_id}/ai-suggest")
def ai_suggest(
    sheet_id: int,
    question_id: int,
    current_user: dict = Depends(
        require_roles("examiner", "moderator")
    ),
    db: Session = Depends(get_db)
):
    return generate_ai_suggestion(
        db=db,
        sheet_id=sheet_id,
        question_id=question_id,
        examiner_id=int(current_user["sub"])
    )


@router.get("/{sheet_id}/questions/{question_id}/ai-suggest")
def latest_ai_suggest(
    sheet_id: int,
    question_id: int,
    current_user: dict = Depends(
        require_roles("examiner", "moderator", "admin")
    ),
    db: Session = Depends(get_db)
):
    return get_latest_ai_suggestion(
        db=db,
        sheet_id=sheet_id,
        question_id=question_id
    )