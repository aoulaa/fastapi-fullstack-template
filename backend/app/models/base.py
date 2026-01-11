from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, text
from sqlalchemy.orm import Mapped, MappedAsDataclass, mapped_column

from app.core.db import Base


class IDMixin(MappedAsDataclass):
    id: Mapped[int] = mapped_column(autoincrement=True, primary_key=True, init=False)


class TimestampMixin(MappedAsDataclass):
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default_factory=lambda: datetime.now(UTC), server_default=text("current_timestamp(0)")
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
        onupdate=datetime.now(UTC),
        server_default=text("current_timestamp(0)"),
    )


class SoftDeleteMixin(MappedAsDataclass):
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, default=None)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, index=True)


class BaseModel(Base, IDMixin, TimestampMixin, SoftDeleteMixin):
    __abstract__ = True
