from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import require_roles
from app.db.database import SessionLocal
from app.models.flag import Flag


router = APIRouter(
    prefix="/flags",
    tags=["Flags"],
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("")
def list_flags(
    status: str | None = None,
    current_user: dict = Depends(require_roles("moderator", "admin")),
    db: Session = Depends(get_db),
):
    query = db.query(Flag)
    if status:
        query = query.filter(Flag.status == status)

    rows = query.order_by(Flag.created_at.desc()).all()

    return [
        {
            "id": row.id,
            "sheet_id": row.sheet_id,
            "question_id": row.question_id,
            "type": row.type,
            "severity": row.severity,
            "reason": row.reason,
            "metric_value": row.metric_value,
            "related_sheet_id": row.related_sheet_id,
            "status": row.status,
            "created_by": row.created_by,
            "created_at": row.created_at,
        }
        for row in rows
    ]
