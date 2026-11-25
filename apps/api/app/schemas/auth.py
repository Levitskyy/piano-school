from datetime import datetime
from typing import Annotated
from uuid import UUID
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

Password = Annotated[str, Field(min_length=8, max_length=128)]


def validate_timezone(value: str) -> str:
    try:
        ZoneInfo(value)
    except ZoneInfoNotFoundError as exc:
        raise ValueError("Неизвестный часовой пояс") from exc
    return value


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    email: EmailStr
    role: str
    timezone: str
    preferred_language: str
    email_verified_at: datetime | None
    created_at: datetime


class RegisterOut(UserOut):
    verification_email_sent: bool = True
    # Только для локальной разработки: в prod ссылку из письма никто не получает.
    dev_verification_url: str | None = None


class RegisterIn(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    email: EmailStr
    password: Password
    timezone: str = "Europe/Moscow"
    preferred_language: str = Field(default="ru", min_length=2, max_length=10)

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Укажите имя")
        return value

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: EmailStr) -> str:
        return str(value).strip().lower()

    @field_validator("timezone")
    @classmethod
    def check_timezone(cls, value: str) -> str:
        return validate_timezone(value)


class LoginIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: EmailStr) -> str:
        return str(value).strip().lower()


class ForgotPasswordIn(BaseModel):
    email: EmailStr

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: EmailStr) -> str:
        return str(value).strip().lower()


class ForgotPasswordOut(BaseModel):
    message: str
    dev_reset_url: str | None = None


class ResetPasswordIn(BaseModel):
    token: str = Field(min_length=20, max_length=256)
    new_password: Password


class VerifyEmailIn(BaseModel):
    token: str = Field(min_length=20, max_length=256)


class ProfileUpdateIn(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    timezone: str | None = None
    preferred_language: str | None = Field(default=None, min_length=2, max_length=10)

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        if not value:
            raise ValueError("Укажите имя")
        return value

    @field_validator("timezone")
    @classmethod
    def check_timezone(cls, value: str | None) -> str | None:
        return validate_timezone(value) if value is not None else None


class MessageOut(BaseModel):
    message: str


class ResendVerificationOut(MessageOut):
    verification_email_sent: bool = True
    dev_verification_url: str | None = None
