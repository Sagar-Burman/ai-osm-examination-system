from pathlib import Path

import cv2
import numpy as np
import pymupdf
from sqlalchemy.orm import Session

from app.models.sheet import Sheet, SheetStatus, QCStatus
from app.models.sheet_pages import SheetPage


STORAGE_PAGES = Path("storage/pages")
STORAGE_PAGES.mkdir(parents=True, exist_ok=True)


def calculate_blur_score(gray_image) -> float:
    return float(
        cv2.Laplacian(gray_image, cv2.CV_64F).var()
    )


def calculate_brightness(gray_image) -> float:
    return float(np.mean(gray_image))


def calculate_contrast(gray_image) -> float:
    return float(np.std(gray_image))


def calculate_ink_ratio(gray_image) -> float:
    _, binary = cv2.threshold(
        gray_image,
        200,
        255,
        cv2.THRESH_BINARY_INV
    )

    return float(
        np.count_nonzero(binary) / binary.size
    )


def calculate_skew_angle(gray_image) -> float:
    binary = cv2.threshold(
        gray_image,
        200,
        255,
        cv2.THRESH_BINARY_INV
    )[1]

    points = cv2.findNonZero(binary)

    if points is None or len(points) < 5:
        return 0.0

    rect = cv2.minAreaRect(points)
    angle = rect[-1]

    if angle < -45:
        angle += 90

    return float(angle)


def analyze_page(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    return {
        "blur_score": calculate_blur_score(gray),
        "brightness": calculate_brightness(gray),
        "contrast": calculate_contrast(gray),
        "skew_angle": calculate_skew_angle(gray),
        "ink_ratio": calculate_ink_ratio(gray),
    }


def run_sheet_qc(
    db: Session,
    sheet_id: int,
    *,
    blur_min: float | None = None,
    brightness_min: float | None = None,
    brightness_max: float | None = None,
    contrast_min: float | None = None,
    ink_ratio_min: float | None = None,
    skew_max: float | None = None,
):
    sheet = db.query(Sheet).filter(Sheet.id == sheet_id).first()

    if sheet is None:
        raise ValueError("Sheet not found")

    document = pymupdf.open(sheet.file_path)

    # Remove previous page-QC rows if QC is rerun.
    db.query(SheetPage).filter(
        SheetPage.sheet_id == sheet_id
    ).delete()

    needs_review = False

    for page_index in range(len(document)):
        page_no = page_index + 1

        page = document[page_index]

        matrix = pymupdf.Matrix(200 / 72, 200 / 72)
        pix = page.get_pixmap(matrix=matrix, alpha=False)

        image = np.frombuffer(
            pix.samples,
            dtype=np.uint8
        ).reshape(
            pix.height,
            pix.width,
            pix.n
        )

        if pix.n == 4:
            image = cv2.cvtColor(
                image,
                cv2.COLOR_RGBA2BGR
            )
        else:
            image = cv2.cvtColor(
                image,
                cv2.COLOR_RGB2BGR
            )

        metrics = analyze_page(image)

        reasons = []

        if blur_min is not None and metrics["blur_score"] < blur_min:
            reasons.append("Blur below configured threshold")

        if (
            brightness_min is not None
            and metrics["brightness"] < brightness_min
        ):
            reasons.append("Brightness below configured threshold")

        if (
            brightness_max is not None
            and metrics["brightness"] > brightness_max
        ):
            reasons.append("Brightness above configured threshold")

        if (
            contrast_min is not None
            and metrics["contrast"] < contrast_min
        ):
            reasons.append("Contrast below configured threshold")

        if (
            ink_ratio_min is not None
            and metrics["ink_ratio"] < ink_ratio_min
        ):
            reasons.append("Possible blank page")

        if (
            skew_max is not None
            and abs(metrics["skew_angle"]) > skew_max
        ):
            reasons.append("Skew above configured threshold")

        qc_flag = "; ".join(reasons) if reasons else None

        if reasons:
            needs_review = True

        image_path = (
            STORAGE_PAGES
            / f"sheet_{sheet_id}_page_{page_no}.png"
        )

        cv2.imwrite(
            str(image_path),
            image
        )

        page_record = SheetPage(
            sheet_id=sheet_id,
            page_no=page_no,
            image_path=str(image_path),
            blur_score=metrics["blur_score"],
            brightness=metrics["brightness"],
            skew_angle=metrics["skew_angle"],
            qc_flag=qc_flag,
            is_cover=(page_no == sheet.cover_page_no),
        )

        db.add(page_record)

    document.close()

    sheet.qc_status = (
        QCStatus.NEEDS_REVIEW
        if needs_review
        else QCStatus.PASS
    )

    sheet.status = (
        SheetStatus.QC_NEEDS_REVIEW
        if needs_review
        else SheetStatus.QC_PASSED
    )

    sheet.page_count = len(
        db.query(SheetPage)
        .filter(SheetPage.sheet_id == sheet_id)
        .all()
    )

    db.commit()

    return {
        "sheet_id": sheet_id,
        "qc_status": sheet.qc_status.value,
        "status": sheet.status.value,
    }