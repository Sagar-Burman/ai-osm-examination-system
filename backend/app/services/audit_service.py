from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.audit import AuditLog


def write_audit(
    db: Session,
    *,
    user_id: int | None,
    role: str,
    action: str,
    entity_type: str,
    entity_id: int,
    old_value: dict | None = None,
    new_value: dict | None = None,
    ip: str | None = None,
    commit: bool = False,
) -> AuditLog:
    """Append one audit event. Audit rows are never updated or deleted."""
    event = AuditLog(
        user_id=user_id,
        role=role,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        old_value=old_value,
        new_value=new_value,
        ip=ip,
        timestamp=datetime.utcnow(),
    )
    db.add(event)
    db.flush()
    if commit:
        db.commit()
        db.refresh(event)
    return event


def list_audit_logs(
    db: Session,
    *,
    user_id: int | None = None,
    entity_type: str | None = None,
    entity_id: int | None = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    limit: int = 200,
) -> list[dict]:
    query = db.query(AuditLog)

    if user_id is not None:
        query = query.filter(AuditLog.user_id == user_id)
    if entity_type is not None:
        query = query.filter(AuditLog.entity_type == entity_type)
    if entity_id is not None:
        query = query.filter(AuditLog.entity_id == entity_id)
    if start_date is not None:
        query = query.filter(AuditLog.timestamp >= start_date)
    if end_date is not None:
        query = query.filter(AuditLog.timestamp <= end_date)

    rows = (
        query.order_by(AuditLog.timestamp.desc(), AuditLog.id.desc())
        .limit(limit)
        .all()
    )

    return [
        {
            "id": row.id,
            "user_id": row.user_id,
            "role": row.role,
            "action": row.action,
            "entity_type": row.entity_type,
            "entity_id": row.entity_id,
            "old_value": row.old_value,
            "new_value": row.new_value,
            "ip": row.ip,
            "timestamp": row.timestamp,
        }
        for row in rows
    ]
