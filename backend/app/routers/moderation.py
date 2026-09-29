from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.core.deps import require_roles
from app.db.database import SessionLocal
from app.schemas.moderation import ModerationDecisionRequest
from app.services.moderation_service import (
    apply_moderation_decision,
    get_moderation_context,
    get_moderation_queue,
)


router = APIRouter(
    prefix="/moderation",
    tags=["Moderation"],
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/queue")
def moderation_queue(
    current_user: dict = Depends(require_roles("moderator")),
    db: Session = Depends(get_db),
):
    return get_moderation_queue(db)


@router.get("/sheets/{sheet_id}")
def moderation_sheet_context(
    sheet_id: int,
    current_user: dict = Depends(require_roles("moderator")),
    db: Session = Depends(get_db),
):
    return get_moderation_context(db, sheet_id)


@router.post("/sheets/{sheet_id}/decision")
def moderation_decision(
    sheet_id: int,
    payload: ModerationDecisionRequest,
    request: Request,
    current_user: dict = Depends(require_roles("moderator")),
    db: Session = Depends(get_db),
):
    return apply_moderation_decision(
        db=db,
        sheet_id=sheet_id,
        moderator_id=int(current_user["sub"]),
        moderator_role=current_user.get("role", "moderator"),
        flag_id=payload.flag_id,
        decision=payload.decision,
        new_marks=payload.new_marks,
        note=payload.note,
        ip=request.client.host if request.client else None,
    )
