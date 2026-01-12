from datetime import datetime
from typing import Annotated, Self

from pydantic import (
    AliasChoices,
    BaseModel,
    BeforeValidator,
    ConfigDict,
    EmailStr,
    Field,
    model_validator,
)

from .base import PersistentDeletion, TimestampSchema


class UserBase(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    name: Annotated[
        str | None,
        Field(
            min_length=2,
            max_length=30,
            examples=["User Userson"],
            validation_alias=AliasChoices("name", "full_name"),
            serialization_alias="full_name",
            default=None,
        ),
    ]
    username: Annotated[
        str | None,
        Field(
            min_length=2,
            max_length=20,
            pattern=r"^[a-z0-9]+$",
            examples=["userson"],
            default=None,
        ),
    ]
    email: Annotated[EmailStr, Field(examples=["user.userson@example.com"])]


class User(TimestampSchema, UserBase, PersistentDeletion):
    profile_image_url: Annotated[str, Field(default="https://www.profileimageurl.com")]
    hashed_password: str
    is_superuser: bool = False
    is_active: bool = True


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: Annotated[str, BeforeValidator(lambda v: str(v)), Field(examples=["1"])]

    full_name: Annotated[str, Field(min_length=2, max_length=30, examples=["User Userson"], validation_alias="name")]
    username: Annotated[str, Field(min_length=2, max_length=20, pattern=r"^[a-z0-9]+$", examples=["userson"])]
    email: Annotated[EmailStr, Field(examples=["user.userson@example.com"])]
    profile_image_url: str
    is_active: bool
    is_superuser: bool


class UserCreate(UserBase):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    password: Annotated[str, Field(pattern=r"^.{8,}|[0-9]+|[A-Z]+|[a-z]+|[^a-zA-Z0-9]+$", examples=["Str1ngst!"])]
    confirm_password: str | None = Field(default=None, exclude=True)
    is_superuser: bool = False
    is_active: bool = True

    @model_validator(mode="after")
    def verify_password_match(self) -> Self:
        if self.confirm_password is not None and self.password != self.confirm_password:
            raise ValueError("Passwords do not match")
        return self


class UserCreateInternal(UserBase):
    hashed_password: str


class UserUpdate(BaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    name: Annotated[
        str | None,
        Field(
            min_length=2,
            max_length=30,
            examples=["User Userberg"],
            default=None,
            validation_alias=AliasChoices("name", "full_name"),
            serialization_alias="full_name",
        ),
    ]
    username: Annotated[
        str | None, Field(min_length=2, max_length=20, pattern=r"^[a-z0-9]+$", examples=["userberg"], default=None)
    ]
    email: Annotated[EmailStr | None, Field(examples=["user.userberg@example.com"], default=None)]
    profile_image_url: Annotated[
        str | None,
        Field(
            pattern=r"^(https?|ftp)://[^\s/$.?#].[^\s]*$", examples=["https://www.profileimageurl.com"], default=None
        ),
    ]
    password: str | None = Field(default=None, min_length=8)
    confirm_password: str | None = Field(default=None, exclude=True)
    is_active: bool | None = None
    is_superuser: bool | None = None

    @model_validator(mode="after")
    def verify_password_match(self) -> Self:
        if self.password is not None and self.confirm_password is not None:
            if self.password != self.confirm_password:
                raise ValueError("Passwords do not match")
        return self


class UserUpdateInternal(UserUpdate):
    updated_at: datetime


class UserDelete(BaseModel):
    model_config = ConfigDict(extra="forbid")

    is_deleted: bool
    deleted_at: datetime


class UserRestoreDeleted(BaseModel):
    is_deleted: bool


class UpdatePassword(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8)
