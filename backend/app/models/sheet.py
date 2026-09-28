from datetime import datetime
from enum import Enum

from sqlalchemy import DateTime, Enum as SQLEnum, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class SheetStatus(str, Enum):
    UPLOADED = "UPLOADED"
    QC_NEEDS_REVIEW = "QC_NEEDS_REVIEW"
    QC_PASSED = "QC_PASSED"
    ANONYMIZED = "ANONYMIZED"
    PROCESSED = "PROCESSED"
    ALLOCATED = "ALLOCATED"
    IN_EVALUATION = "IN_EVALUATION"
    SUBMITTED = "SUBMITTED"
    FLAGGED = "FLAGGED"
    IN_MODERATION = "IN_MODERATION"
    MODERATED = "MODERATED"
    APPROVED = "APPROVED"
    RESULT_READY = "RESULT_READY"


class QCStatus(str, Enum):
    PASS = "PASS"
    NEEDS_REVIEW = "NEEDS_REVIEW"


class ProcessingStatus(str, Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    DONE = "DONE"
    FAILED = "FAILED"


class Sheet(Base):
    __tablename__ = "sheets"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True
    )

    exam_id: Mapped[int] = mapped_column(
        ForeignKey("exams.id"),
        nullable=False
    )

    anonymous_code: Mapped[str | None] = mapped_column(
        String(20),
        unique=True,
        nullable=True
    )

    file_path: Mapped[str] = mapped_column(
        String(500),
        nullable=False
    )

    page_count: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True
    )

    cover_page_no: Mapped[int] = mapped_column(
        Integer,
        default=1,
        nullable=False
    )

    status: Mapped[SheetStatus] = mapped_column(
        SQLEnum(SheetStatus),
        default=SheetStatus.UPLOADED,
        nullable=False
    )

    qc_status: Mapped[QCStatus | None] = mapped_column(
        SQLEnum(QCStatus),
        nullable=True
    )

    processing_status: Mapped[ProcessingStatus] = mapped_column(
        SQLEnum(ProcessingStatus),
        default=ProcessingStatus.PENDING,
        nullable=False
    )

    uploaded_by: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False
    )

    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    submitted_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True
    )

    total_marks: Mapped[float | None] = mapped_column(
        nullable=True
    )