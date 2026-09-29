from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import require_roles
from app.db.database import SessionLocal
from app.services.submission_service import check_submission, submit_sheet


router = APIRouter(
    prefix="/sheets",
    tags=["Submission"],
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/{sheet_id}/submission-check")
def submission_check(
    sheet_id: int,
    current_user: dict = Depends(require_roles("examiner")),
    db: Session = Depends(get_db),
):
    return check_submission(
        db=db,
        sheet_id=sheet_id,
        examiner_id=int(current_user["sub"]),
    )


@router.post("/{sheet_id}/submit")
def submit(
    sheet_id: int,
    current_user: dict = Depends(require_roles("examiner")),
    db: Session = Depends(get_db),
):
    return submit_sheet(
        db=db,
        sheet_id=sheet_id,
        examiner_id=int(current_user["sub"]),
    )
