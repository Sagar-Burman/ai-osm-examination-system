from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class IdentityMap(Base):
    __tablename__ = "identity_map"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True
    )

    sheet_id: Mapped[int] = mapped_column(
        ForeignKey("sheets.id"),
        unique=True,
        nullable=False
    )

    roll_no: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    anonymous_code: Mapped[str | None] = mapped_column(
        String(20),
        unique=True,
        nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )