from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.analytics.aggregates import get_dashboard_stats
from app.analytics.examiner_stats import (
    get_all_examiner_stats,
    get_examiner_stats,
)
from app.core.deps import get_current_user, require_role
from app.db.database import SessionLocal


router = APIRouter(
    prefix="/analytics",
    tags=["Analytics"],
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/dashboard")
def analytics_dashboard(
    exam_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role("admin")),
):
    try:
        return get_dashboard_stats(db, exam_id)
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Dashboard analytics error: {type(exc).__name__}: {exc}",
        )


@router.get("/examiners")
def examiner_analytics(
    exam_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role("admin")),
):
    try:
        return get_all_examiner_stats(db, exam_id)
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Examiner analytics error: {type(exc).__name__}: {exc}",
        )


@router.get("/examiners/me")
def my_examiner_analytics(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role("examiner")),
):
    examiner_id = current_user.get("sub")

    if examiner_id is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid token: examiner id missing.",
        )

    try:
        examiner_id = int(examiner_id)
    except (TypeError, ValueError):
        raise HTTPException(
            status_code=401,
            detail="Invalid token: examiner id is invalid.",
        )

    try:
        return get_examiner_stats(db, examiner_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Examiner analytics error: {type(exc).__name__}: {exc}",
        )
