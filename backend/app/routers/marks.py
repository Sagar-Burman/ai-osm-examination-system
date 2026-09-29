from fastapi import APIRouter, Body, Depends
from sqlalchemy.orm import Session

from app.core.deps import require_roles
from app.db.database import SessionLocal
from app.services.mark_service import (
    get_marks,
    save_mark,
    confirm_blank
)


router = APIRouter(
    prefix="/sheets",
    tags=["Marking"]
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/{sheet_id}/marks")
def get_sheet_marks(
    sheet_id: int,
    current_user: dict = Depends(
        require_roles("examiner", "moderator")
    ),
    db: Session = Depends(get_db)
):
    role = current_user.get("role")
    examiner_id = int(current_user["sub"])

    return get_marks(
        db=db,
        sheet_id=sheet_id,
        examiner_id=examiner_id,
        allow_moderator=(role == "moderator")
    )


@router.put("/{sheet_id}/marks/{question_id}")
def update_mark(
    sheet_id: int,
    question_id: int,
    final_marks: float = Body(...),
    comment: str | None = Body(None),
    ai_suggestion_id: int | None = Body(None),
    ai_action: str = Body("NONE"),
    current_user: dict = Depends(
        require_roles("examiner")
    ),
    db: Session = Depends(get_db)
):
    return save_mark(
        db=db,
        sheet_id=sheet_id,
        question_id=question_id,
        final_marks=final_marks,
        comment=comment,
        ai_suggestion_id=ai_suggestion_id,
        ai_action=ai_action,
        examiner_id=int(current_user["sub"])
    )


@router.put("/{sheet_id}/marks/{question_id}/blank")
def mark_blank(
    sheet_id: int,
    question_id: int,
    current_user: dict = Depends(
        require_roles("examiner")
    ),
    db: Session = Depends(get_db)
):
    return confirm_blank(
        db=db,
        sheet_id=sheet_id,
        question_id=question_id,
        examiner_id=int(current_user["sub"])
    )