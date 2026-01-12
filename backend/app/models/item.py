from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import BaseModel

if TYPE_CHECKING:
    from .user import User


class Item(BaseModel):
    __tablename__ = "item"

    title: Mapped[str] = mapped_column(String(255), nullable=False, kw_only=True)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True, default=None, kw_only=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"), nullable=False, kw_only=True)

    # Relationship
    owner: Mapped["User"] = relationship("User", back_populates="items", init=False)  # type: ignore
