"""ProductImage SQLAlchemy model."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from src.app.extensions import db


class ProductImageModel(db.Model):  # type: ignore[name-defined]
    __tablename__ = "product_images"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    product_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True
    )
    file_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    is_primary: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc), server_default=func.now()
    )
