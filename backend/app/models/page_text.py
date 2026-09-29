from sqlalchemy import Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class PageText(Base):
    __tablename__ = "page_text"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True
    )

    sheet_id: Mapped[int] = mapped_column(
        ForeignKey("sheets.id"),
        nullable=False
    )

    page_no: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    raw_text: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    ocr_confidence: Mapped[float | None] = mapped_column(
        Float,
        nullable=True
    )

    ocr_status: Mapped[str] = mapped_column(
        String(20),
        nullable=False
    )

    model_version: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True
    )

    prompt_version: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True
    )