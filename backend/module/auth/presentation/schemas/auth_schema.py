from __future__ import annotations

from pydantic import BaseModel
from pydantic import EmailStr
from pydantic import Field
from datetime import datetime
from uuid import UUID

from module.auth.domain.enums.auth_provider import AuthProvider
from module.auth.domain.enums.authentication_context_type import (
    AuthenticationContextType,
)


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


class VerifyEmailSchema(BaseModel):
    token: str = Field(min_length=32)


class VerifyEmailResponseSchema(BaseModel):
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


class OidcStartResponseSchema(BaseModel):
    authorization_url: str


class KnowledgeSpaceAuthRequirementSchema(BaseModel):
    auth_method: AuthProvider
    require_mfa: bool


class VerifyMfaSchema(BaseModel):
    challenge_id: str = Field(min_length=32)
    code: str = Field(pattern=r"^\d{6}$")


class CurrentUserSchema(
    BaseModel,
):
    user_id: UUID
    email: str
    context_type: AuthenticationContextType
    auth_method: AuthProvider
    knowledge_space_id: UUID | None
    authenticated_at: datetime
    mfa_verified: bool
