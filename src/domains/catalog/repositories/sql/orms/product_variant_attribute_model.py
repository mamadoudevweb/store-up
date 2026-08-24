"""ProductVariantAttribute SQLAlchemy model."""
from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from src.app.extensions import db


class ProductVariantAttributeModel(db.Model):  # type: ignore[name-defined]
    __tablename__ = "product_variant_attributes"
    __table_args__ = (
        UniqueConstraint("variant_id", "attribute_id", name="uq_variant_attribute"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    variant_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("product_variants.id", ondelete="CASCADE"), nullable=False, index=True
    )
    attribute_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("attributes.id", ondelete="RESTRICT"), nullable=False
    )
    attribute_value_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("attribute_values.id", ondelete="RESTRICT"), nullable=False
    )
