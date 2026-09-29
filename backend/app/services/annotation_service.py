from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.annotation import Annotation
from app.models.sheet import Sheet
from app.models.sheet_pages import SheetPage
from app.schemas.annotations import AnnotationCreate


def _get_sheet(db: Session, sheet_id: int) -> Sheet:
    sheet = (
        db.query(Sheet)
        .filter(Sheet.id == sheet_id)
        .first()
    )

    if sheet is None:
        raise HTTPException(
            status_code=404,
            detail="Sheet not found.",
        )

    return sheet


def _ensure_examiner_assigned(
    db: Session,
    sheet_id: int,
    examiner_id: int,
) -> None:
    from app.models.assignment import Assignment

    assignment = (
        db.query(Assignment)
        .filter(
            Assignment.sheet_id == sheet_id,
            Assignment.examiner_id == examiner_id,
        )
        .first()
    )

    if assignment is None:
        raise HTTPException(
            status_code=403,
            detail="Sheet is not assigned to this examiner.",
        )


def create_annotation(
    db: Session,
    sheet_id: int,
    examiner_id: int,
    payload: AnnotationCreate,
) -> Annotation:

    sheet = _get_sheet(db, sheet_id)

    _ensure_examiner_assigned(
        db,
        sheet_id,
        examiner_id,
    )

    if sheet.status not in (
        "ALLOCATED",
        "IN_EVALUATION",
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Annotations are available only "
                "while the sheet is under evaluation."
            ),
        )

    page = (
        db.query(SheetPage)
        .filter(
            SheetPage.sheet_id == sheet_id,
            SheetPage.page_no == payload.page_no,
        )
        .first()
    )

    if page is None:
        raise HTTPException(
            status_code=422,
            detail="Page does not exist for this sheet.",
        )

    if (
        payload.w is not None
        and payload.x + payload.w > 1
    ):
        raise HTTPException(
            status_code=422,
            detail="Annotation width exceeds page bounds.",
        )

    if (
        payload.h is not None
        and payload.y + payload.h > 1
    ):
        raise HTTPException(
            status_code=422,
            detail="Annotation height exceeds page bounds.",
        )

    annotation = Annotation(
        sheet_id=sheet_id,
        page_no=payload.page_no,
        question_id=payload.question_id,
        type=payload.type,
        x=payload.x,
        y=payload.y,
        w=payload.w,
        h=payload.h,
        text=payload.text,
        examiner_id=examiner_id,
    )

    db.add(annotation)
    db.commit()
    db.refresh(annotation)

    return annotation


def list_annotations(
    db: Session,
    sheet_id: int,
    user_id: int,
    role: str,
):
    sheet = _get_sheet(db, sheet_id)

    if role == "examiner":
        _ensure_examiner_assigned(
            db,
            sheet_id,
            user_id,
        )

    elif role != "moderator":
        raise HTTPException(
            status_code=403,
            detail="Examiner or moderator role required.",
        )

    if sheet.status not in (
        "ALLOCATED",
        "IN_EVALUATION",
        "SUBMITTED",
        "FLAGGED",
        "IN_MODERATION",
        "MODERATED",
    ):
        raise HTTPException(
            status_code=409,
            detail="Sheet is not available for annotation review.",
        )

    return (
        db.query(Annotation)
        .filter(
            Annotation.sheet_id == sheet_id,
            Annotation.deleted_at.is_(None),
        )
        .order_by(
            Annotation.page_no,
            Annotation.id,
        )
        .all()
    )


def soft_delete_annotation(
    db: Session,
    annotation_id: int,
    examiner_id: int,
) -> None:

    annotation = (
        db.query(Annotation)
        .filter(Annotation.id == annotation_id)
        .first()
    )

    if annotation is None:
        raise HTTPException(
            status_code=404,
            detail="Annotation not found.",
        )

    if annotation.examiner_id != examiner_id:
        raise HTTPException(
            status_code=403,
            detail="You can delete only your own annotation.",
        )

    if annotation.deleted_at is not None:
        return

    annotation.deleted_at = datetime.utcnow()

    db.commit()