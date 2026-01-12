from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import BaseModel

if TYPE_CHECKING:
    from .item import Item


class User(BaseModel):
    __tablename__ = "user"

    name: Mapped[str | None] = mapped_column(String(30), kw_only=True)
    username: Mapped[str] = mapped_column(String(20), unique=True, index=True, kw_only=True)
    email: Mapped[str] = mapped_column(String(50), unique=True, index=True, kw_only=True)
    hashed_password: Mapped[str] = mapped_column(String, kw_only=True)

    profile_image_url: Mapped[str] = mapped_column(String, default="https://profileimageurl.com", kw_only=True)
    is_active: Mapped[bool] = mapped_column(default=True, kw_only=True)
    is_superuser: Mapped[bool] = mapped_column(default=False, kw_only=True)

    # Relationships
    items: Mapped[list["Item"]] = relationship("Item", back_populates="owner", cascade="all, delete-orphan", init=False)  # type: ignore
