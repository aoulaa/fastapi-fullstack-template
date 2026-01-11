from datetime import datetime

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import BaseModel


class TokenBlacklist(BaseModel):
    __tablename__ = "token_blacklist"

    token: Mapped[str] = mapped_column(String, unique=True, index=True, kw_only=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime, kw_only=True)
