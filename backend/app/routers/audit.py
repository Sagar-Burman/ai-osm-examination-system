from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.deps import require_roles
from app.db.database import SessionLocal
from app.services.audit_service import list_audit_logs


router = APIRouter(
    prefix="/audit",
    tags=["Audit"],
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("")
def get_audit_logs(
    user_id: int | None = Query(default=None),
    entity_type: str | None = Query(default=None),
    entity_id: int | None = Query(default=None),
    start_date: datetime | None = Query(default=None),
    end_date: datetime | None = Query(default=None),
    limit: int = Query(default=200, ge=1, le=1000),
    current_user: dict = Depends(require_roles("admin")),
    db: Session = Depends(get_db),
):
    return list_audit_logs(
        db,
        user_id=user_id,
        entity_type=entity_type,
        entity_id=entity_id,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
    )
