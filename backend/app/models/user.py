from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from .base import BaseModel


class User(BaseModel):
    __tablename__ = "user"

    name: Mapped[str] = mapped_column(String(30), kw_only=True)
    username: Mapped[str] = mapped_column(String(20), unique=True, index=True, kw_only=True)
    email: Mapped[str] = mapped_column(String(50), unique=True, index=True, kw_only=True)
    hashed_password: Mapped[str] = mapped_column(String, kw_only=True)

    profile_image_url: Mapped[str] = mapped_column(String, default="https://profileimageurl.com", kw_only=True)
    is_superuser: Mapped[bool] = mapped_column(default=False, kw_only=True)
