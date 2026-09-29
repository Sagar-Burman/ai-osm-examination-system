from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.db.database import SessionLocal
from app.schemas.annotations import AnnotationCreate, AnnotationResponse
from app.services.annotation_service import (
    create_annotation,
    list_annotations,
    soft_delete_annotation,
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


router = APIRouter(tags=["Annotations"])


@router.post(
    "/sheets/{sheet_id}/annotations",
    response_model=AnnotationResponse,
    status_code=201,
)
def create_sheet_annotation(
    sheet_id: int,
    payload: AnnotationCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    if current_user.get("role") != "examiner":
        raise HTTPException(
            status_code=403,
            detail="Examiner role required.",
        )

    try:
        examiner_id = int(current_user["sub"])
        return create_annotation(
            db,
            sheet_id,
            examiner_id,
            payload,
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Annotation POST error: {type(exc).__name__}: {exc}",
        )


@router.get("/sheets/{sheet_id}/annotations")
def get_sheet_annotations(
    sheet_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    role = current_user.get("role")

    if role not in ("examiner", "moderator"):
        raise HTTPException(
            status_code=403,
            detail="Examiner or moderator role required.",
        )

    try:
        user_id = int(current_user["sub"])
        return list_annotations(
            db,
            sheet_id,
            user_id,
            role,
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Annotation GET error: {type(exc).__name__}: {exc}",
        )


@router.delete("/annotations/{annotation_id}")
def delete_annotation(
    annotation_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    if current_user.get("role") != "examiner":
        raise HTTPException(
            status_code=403,
            detail="Examiner role required.",
        )

    try:
        examiner_id = int(current_user["sub"])
        soft_delete_annotation(
            db,
            annotation_id,
            examiner_id,
        )
        return {"status": "DELETED"}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Annotation DELETE error: {type(exc).__name__}: {exc}",
        )
