from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    UploadFile,
    status,
    HTTPException
)
from sqlalchemy.orm import Session

from app.core.deps import require_roles
from app.db.database import SessionLocal
from app.schemas.sheet import SheetUploadResponse
from app.services.sheet_service import upload_sheet, anonymize_sheet
from app.services.qc_service import run_sheet_qc


router = APIRouter(
    prefix="/sheets",
    tags=["Sheets"]
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ---------------------------------------------------------
# Upload scanned answer sheet
# ---------------------------------------------------------
@router.post(
    "",
    response_model=SheetUploadResponse,
    status_code=status.HTTP_201_CREATED
)
async def upload_sheet_api(
    file: UploadFile = File(...),
    exam_id: int = Form(...),
    roll_no: str = Form(...),
    cover_page_no: int = Form(1),
    current_user: dict = Depends(
        require_roles("operator", "admin")
    ),
    db: Session = Depends(get_db)
):
    return await upload_sheet(
        db=db,
        file=file,
        exam_id=exam_id,
        roll_no=roll_no,
        cover_page_no=cover_page_no,
        uploaded_by=int(current_user["sub"])
    )


# ---------------------------------------------------------
# Scan Quality Check
# ---------------------------------------------------------
@router.get("/{sheet_id}/qc")
def get_sheet_qc(
    sheet_id: int,
    current_user: dict = Depends(
        require_roles("operator", "admin")
    ),
    db: Session = Depends(get_db)
):
    try:
        return run_sheet_qc(
            db=db,
            sheet_id=sheet_id
        )
    except ValueError as e:
        raise HTTPException(
            status_code=404,
            detail=str(e)
        )


# ---------------------------------------------------------
# Anonymization
# ---------------------------------------------------------
@router.post("/{sheet_id}/anonymize")
def anonymize_sheet_api(
    sheet_id: int,
    current_user: dict = Depends(
        require_roles("admin")
    ),
    db: Session = Depends(get_db)
):
    return anonymize_sheet(
        db=db,
        sheet_id=sheet_id
    )