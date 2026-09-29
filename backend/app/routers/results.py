from fastapi import APIRouter, Depends, Request, Response, Query
from sqlalchemy.orm import Session

from app.core.deps import require_roles
from app.db.database import SessionLocal
from app.schemas.results import ResultSheetIds
from app.services.result_service import (
    approve_results,
    export_results,
    get_readiness,
    release_results,
)


router = APIRouter(prefix="/results", tags=["Results"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/readiness")
def results_readiness(
    exam_id: int = Query(...),
    current_user: dict = Depends(require_roles("admin")),
    db: Session = Depends(get_db),
):
    return get_readiness(db, exam_id)


@router.post("/approve")
def results_approve(
    payload: ResultSheetIds,
    request: Request,
    current_user: dict = Depends(require_roles("admin")),
    db: Session = Depends(get_db),
):
    return approve_results(
        db,
        sheet_ids=payload.sheet_ids,
        admin_id=int(current_user["sub"]),
        role=current_user.get("role", "admin"),
        ip=request.client.host if request.client else None,
    )


@router.post("/release")
def results_release(
    payload: ResultSheetIds,
    request: Request,
    current_user: dict = Depends(require_roles("admin")),
    db: Session = Depends(get_db),
):
    return release_results(
        db,
        sheet_ids=payload.sheet_ids,
        admin_id=int(current_user["sub"]),
        role=current_user.get("role", "admin"),
        ip=request.client.host if request.client else None,
    )


@router.get("/export")
def results_export(
    exam_id: int = Query(...),
    current_user: dict = Depends(require_roles("admin")),
    db: Session = Depends(get_db),
):
    csv_text = export_results(db, exam_id=exam_id)
    return Response(
        content=csv_text,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=results_exam_{exam_id}.csv"},
    )
