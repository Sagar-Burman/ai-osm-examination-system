from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import require_roles
from app.db.database import SessionLocal
from app.models.page_text import PageText
from app.models.sheet import ProcessingStatus, Sheet, SheetStatus
from app.ai.ocr_service import process_sheet_ocr


router = APIRouter(
    prefix="/sheets",
    tags=["OCR"]
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ---------------------------------------------------------
# Start OCR
# ---------------------------------------------------------
@router.post("/{sheet_id}/ocr")
def start_ocr(
    sheet_id: int,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(
        require_roles("admin")
    ),
    db: Session = Depends(get_db)
):
    sheet = (
        db.query(Sheet)
        .filter(Sheet.id == sheet_id)
        .first()
    )

    if sheet is None:
        raise HTTPException(
            status_code=404,
            detail="Sheet not found"
        )

    if sheet.status != SheetStatus.ANONYMIZED:
        raise HTTPException(
            status_code=409,
            detail="Sheet is not ready for OCR"
        )

    if sheet.processing_status == ProcessingStatus.PROCESSING:
        raise HTTPException(
            status_code=409,
            detail="ALREADY_PROCESSING"
        )

    sheet.processing_status = ProcessingStatus.PENDING
    db.commit()

    background_tasks.add_task(
        process_sheet_ocr,
        sheet_id
    )

    return {
        "sheet_id": sheet_id,
        "status": "PENDING"
    }


# ---------------------------------------------------------
# OCR status
# ---------------------------------------------------------
@router.get("/{sheet_id}/ocr/status")
def get_ocr_status(
    sheet_id: int,
    current_user: dict = Depends(
        require_roles(
            "examiner",
            "moderator",
            "admin"
        )
    ),
    db: Session = Depends(get_db)
):
    sheet = (
        db.query(Sheet)
        .filter(Sheet.id == sheet_id)
        .first()
    )

    if sheet is None:
        raise HTTPException(
            status_code=404,
            detail="Sheet not found"
        )

    pages = (
        db.query(PageText)
        .filter(PageText.sheet_id == sheet_id)
        .order_by(PageText.page_no)
        .all()
    )

    return {
        "status": sheet.processing_status.value,
        "pages": [
            {
                "page_no": page.page_no,
                "status": page.ocr_status,
                "confidence": page.ocr_confidence
            }
            for page in pages
        ]
    }


# ---------------------------------------------------------
# OCR text for one page
# ---------------------------------------------------------
@router.get("/{sheet_id}/pages/{page_no}/text")
def get_page_text(
    sheet_id: int,
    page_no: int,
    current_user: dict = Depends(
        require_roles(
            "examiner",
            "moderator",
            "admin"
        )
    ),
    db: Session = Depends(get_db)
):
    sheet = (
        db.query(Sheet)
        .filter(Sheet.id == sheet_id)
        .first()
    )

    if sheet is None:
        raise HTTPException(
            status_code=404,
            detail="Sheet not found"
        )

    page_text = (
        db.query(PageText)
        .filter(
            PageText.sheet_id == sheet_id,
            PageText.page_no == page_no
        )
        .first()
    )

    if page_text is None:
        raise HTTPException(
            status_code=404,
            detail="OCR text not found"
        )

    return {
        "sheet_id": sheet_id,
        "page_no": page_no,
        "raw_text": page_text.raw_text,
        "ocr_confidence": page_text.ocr_confidence,
        "ocr_status": page_text.ocr_status,
        "model_version": page_text.model_version,
        "prompt_version": page_text.prompt_version
    }