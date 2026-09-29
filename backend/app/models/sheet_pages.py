from sqlalchemy import Boolean, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class SheetPage(Base):
    __tablename__ = "sheet_pages"

    id: Mapped[int] = mapped_column(
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

    image_path: Mapped[str] = mapped_column(
        String(500),
        nullable=False
    )

    blur_score: Mapped[float | None] = mapped_column(
        Float,
        nullable=True
    )

    brightness: Mapped[float | None] = mapped_column(
        Float,
        nullable=True
    )

    skew_angle: Mapped[float | None] = mapped_column(
        Float,
        nullable=True
    )

    qc_flag: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True
    )

    is_cover: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False
    )