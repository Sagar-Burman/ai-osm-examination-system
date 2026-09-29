import secrets

from pathlib import Path

import pymupdf

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.models.exam import Exam
from app.models.identity import IdentityMap
from app.models.sheet import Sheet, SheetStatus
from app.schemas.sheet import SheetUploadResponse


ALLOWED_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png"}
MAX_FILE_SIZE = 25 * 1024 * 1024

STORAGE_DIR = Path("storage/uploads")
STORAGE_DIR.mkdir(parents=True, exist_ok=True)


async def upload_sheet(
    db: Session,
    file: UploadFile,
    exam_id: int,
    roll_no: str,
    cover_page_no: int,
    uploaded_by: int
) -> SheetUploadResponse:

    # Check exam
    exam = (
        db.query(Exam)
        .filter(Exam.id == exam_id)
        .first()
    )

    if exam is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exam not found"
        )

    # Basic roll number validation
    if not roll_no.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid roll number"
        )

    # Validate extension
    original_name = file.filename or ""
    extension = Path(original_name).suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="UNSUPPORTED_FILE_TYPE"
        )

    # Read file
    file_data = await file.read()

    if len(file_data) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="FILE_TOO_LARGE"
        )

    if not file_data:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="CORRUPT_FILE"
        )

    # Validate magic bytes
    valid_magic = False

    if extension == ".pdf":
        valid_magic = file_data.startswith(b"%PDF-")

    elif extension in {".jpg", ".jpeg"}:
        valid_magic = file_data.startswith(b"\xff\xd8\xff")

    elif extension == ".png":
        valid_magic = file_data.startswith(
            b"\x89PNG\r\n\x1a\n"
        )

    if not valid_magic:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="CORRUPT_FILE"
        )

    # Validate document and determine page count
    page_count = 1

    try:
        if extension == ".pdf":
            document = pymupdf.open(
                stream=file_data,
                filetype="pdf"
            )

            page_count = len(document)
            document.close()

            if page_count == 0:
                raise ValueError("No pages")

    except Exception:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="CORRUPT_FILE"
        )

    # Cover page number validation
    if cover_page_no < 1 or cover_page_no > page_count:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid cover page number"
        )

    # Duplicate check: same roll number in same exam
    duplicate = (
        db.query(IdentityMap)
        .join(
            Sheet,
            IdentityMap.sheet_id == Sheet.id
        )
        .filter(
            IdentityMap.roll_no == roll_no,
            Sheet.exam_id == exam_id
        )
        .first()
    )

    if duplicate:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="DUPLICATE_ROLL_NO"
        )

    # Random internal filename
    random_name = f"{secrets.token_hex(16)}{extension}"
    file_path = STORAGE_DIR / random_name

    file_path.write_bytes(file_data)

    # Create sheet record
    sheet = Sheet(
        exam_id=exam_id,
        file_path=str(file_path),
        page_count=page_count,
        cover_page_no=cover_page_no,
        status=SheetStatus.UPLOADED,
        uploaded_by=uploaded_by
    )

    db.add(sheet)
    db.commit()
    db.refresh(sheet)

    # Create identity mapping.
    # Anonymous code is generated only after QC PASS.
    identity_map = IdentityMap(
        sheet_id=sheet.id,
        roll_no=roll_no,
        anonymous_code=None
    )

    db.add(identity_map)
    db.commit()

    return SheetUploadResponse(
        sheet_id=sheet.id,
        qc_status="PENDING",
        status=sheet.status.value,
        anonymous_code=None
    )


def anonymize_sheet(
    db: Session,
    sheet_id: int
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

    # Anonymization only after QC PASS
    if sheet.status != SheetStatus.QC_PASSED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Sheet is not ready for anonymization"
        )

    # Get existing identity mapping
    identity_map = (
        db.query(IdentityMap)
        .filter(
            IdentityMap.sheet_id == sheet.id
        )
        .first()
    )

    if identity_map is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Identity mapping not found"
        )

    # Generate unique random EX-##### code
    while True:
        anonymous_code = (
            f"EX-{secrets.randbelow(100000):05d}"
        )

        existing = (
            db.query(Sheet)
            .filter(
                Sheet.anonymous_code == anonymous_code
            )
            .first()
        )

        if existing is None:
            break

    # Store anonymous code in both required records
    identity_map.anonymous_code = anonymous_code
    sheet.anonymous_code = anonymous_code
    sheet.status = SheetStatus.ANONYMIZED

    db.commit()
    db.refresh(sheet)

    return {
        "sheet_id": sheet.id,
        "anonymous_code": sheet.anonymous_code,
        "status": sheet.status.value
    }