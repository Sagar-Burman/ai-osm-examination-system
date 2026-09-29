from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.assignment import Assignment
from app.models.sheet import Sheet, SheetStatus
from app.models.user import User


def allocate_sheet(
    db: Session,
    sheet_id: int,
    examiner_id: int,
    assigned_by: int
):
    sheet = (
        db.query(Sheet)
        .filter(Sheet.id == sheet_id)
        .first()
    )

    if sheet is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sheet not found"
        )

    if sheet.status != SheetStatus.PROCESSED:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="SHEET_NOT_READY"
        )

    examiner = (
        db.query(User)
        .filter(
            User.id == examiner_id,
            User.role == "examiner",
            User.is_active == True
        )
        .first()
    )

    if examiner is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="NO_ELIGIBLE_EXAMINER"
        )

    # Examiner cannot receive a sheet they uploaded.
    if sheet.uploaded_by == examiner_id:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Examiner cannot receive a sheet they uploaded"
        )

    existing = (
        db.query(Assignment)
        .filter(Assignment.sheet_id == sheet_id)
        .first()
    )

    if existing:
        existing.examiner_id = examiner_id
        existing.assigned_by = assigned_by
        existing.status = "ASSIGNED"
    else:
        assignment = Assignment(
            sheet_id=sheet_id,
            examiner_id=examiner_id,
            assigned_by=assigned_by,
            status="ASSIGNED"
        )
        db.add(assignment)

    sheet.status = SheetStatus.ALLOCATED

    db.commit()

    assignment = (
        db.query(Assignment)
        .filter(Assignment.sheet_id == sheet_id)
        .first()
    )

    return {
        "sheet_id": sheet_id,
        "examiner_id": assignment.examiner_id,
        "status": sheet.status.value
    }