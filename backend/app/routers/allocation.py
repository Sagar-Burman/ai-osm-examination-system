from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import require_roles
from app.db.database import SessionLocal
from app.services.allocation_service import allocate_sheet


router = APIRouter(
    prefix="/allocations",
    tags=["Allocation"]
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/{sheet_id}")
def allocate_sheet_api(
    sheet_id: int,
    examiner_id: int,
    current_user: dict = Depends(
        require_roles("admin")
    ),
    db: Session = Depends(get_db)
):
    return allocate_sheet(
        db=db,
        sheet_id=sheet_id,
        examiner_id=examiner_id,
        assigned_by=int(current_user["sub"])
    )