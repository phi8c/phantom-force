from __future__ import annotations

from pydantic import BaseModel
from pydantic import EmailStr
from pydantic import Field


class RegisterLocalUserSchema(
    BaseModel,
):
    email: EmailStr
    password: str = Field(
        min_length=12,
    )


class RegisterLocalUserResponseSchema(
    BaseModel,
):
    message: str


class LocalLoginSchema(
    BaseModel,
):
    email: EmailStr
    password: str


class LocalLoginResponseSchema(
    BaseModel,
):
    status: str
    mfa_challenge_id: str | None = None


class CurrentUserSchema(
    BaseModel,
):
    user_id: str
    email: str