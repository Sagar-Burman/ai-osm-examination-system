from enum import Enum

from sqlalchemy import Boolean, Enum as SQLEnum, ForeignKey, Integer, JSON, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class SegmentSource(str, Enum):
    AUTO = "AUTO"
    MANUAL = "MANUAL"


class AnswerSegment(Base):
    __tablename__ = "answer_segments"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True
    )

    sheet_id: Mapped[int] = mapped_column(
        ForeignKey("sheets.id"),
        nullable=False
    )

    question_id: Mapped[int] = mapped_column(
        ForeignKey("questions.id"),
        nullable=False
    )

    page_no: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    region: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True
    )

    text: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    is_blank_detected: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False
    )

    source: Mapped[SegmentSource] = mapped_column(
        SQLEnum(SegmentSource),
        nullable=False
    )