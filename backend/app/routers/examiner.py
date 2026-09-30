from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.deps import require_roles
from app.db.database import SessionLocal
from app.models.assignment import Assignment
from app.models.sheet import Sheet
from app.models.exam import Exam


router = APIRouter(
    prefix="/examiner",
    tags=["Examiner"]
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/queue")
def examiner_queue(
    current_user: dict = Depends(require_roles("examiner")),
    db: Session = Depends(get_db)
):

    
    examiner_id = int(current_user["sub"])

    rows = (
        db.query(Assignment, Sheet, Exam)
        .join(Sheet, Assignment.sheet_id == Sheet.id)
        .join(Exam, Sheet.exam_id == Exam.id)
        .filter(Assignment.examiner_id == examiner_id)
        .all()
    )

    

    return [
        {
            "sheet_id": assignment.sheet_id,
            "anonymous_code": sheet.anonymous_code,
            "exam": exam.name,
            "pages": sheet.page_count,
            "status": sheet.status,
            "progress": 0
        }
        for assignment, sheet, exam in rows
    ]

@router.get("/sheets/{sheet_id}/file")
def examiner_sheet_file(
    sheet_id: int,
    current_user: dict = Depends(require_roles("examiner")),
    db: Session = Depends(get_db)
):
    examiner_id = int(current_user["sub"])

    row = (
        db.query(Assignment, Sheet)
        .join(Sheet, Assignment.sheet_id == Sheet.id)
        .filter(
            Assignment.sheet_id == sheet_id,
            Assignment.examiner_id == examiner_id
        )
        .first()
    )

    if row is None:
        raise HTTPException(
            status_code=404,
            detail="Sheet not assigned to this examiner"
        )

    _, sheet = row

    if not sheet.file_path:
        raise HTTPException(
            status_code=404,
            detail="Sheet file not found"
        )

    return FileResponse(
        path=sheet.file_path,
        media_type="application/pdf"
    )