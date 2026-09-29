from __future__ import annotations

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from bootstrap.database import get_session
from module.auth.application.services.auth_policy_resolver import AuthPolicyResolver
from module.auth.application.services.authentication_context_guard import (
    AuthenticationContextGuard,
)
from module.auth.composition.factory import AuthFoundation, create_auth_foundation
from module.auth.domain.contracts.auth_session_repository import AuthSessionRepository
from module.auth.domain.contracts.clock import Clock
from module.auth.domain.contracts.credential_repository import CredentialRepository
from module.auth.domain.contracts.lockout_policy import LockoutPolicy
from module.auth.domain.contracts.mfa_challenge_store import MfaChallengeStore
from module.auth.domain.contracts.oidc_transaction_store import OidcTransactionStore
from module.auth.domain.contracts.password_hasher import PasswordHasher
from module.auth.domain.contracts.token_service import TokenService
from module.auth.domain.contracts.unit_of_work import UnitOfWork
from module.auth.domain.contracts.verification_token_repository import (
    VerificationTokenRepository,
)
from module.auth.domain.contracts.verification_email_sender import (
    VerificationEmailSender,
)
from module.auth.domain.services.password_policy import PasswordPolicy
from module.auth.domain.services.reauthentication_policy import ReauthenticationPolicy
from module.auth.domain.services.session_expiry_policy import SessionExpiryPolicy
from module.auth.domain.services.verification_token_policy import VerificationTokenPolicy
from module.user.facade.contract import UserModuleFacade
from shared.config.settings import settings


def get_auth_foundation(
    session: AsyncSession = Depends(get_session),
) -> AuthFoundation:
    return create_auth_foundation(session)


def get_unit_of_work(
    foundation: AuthFoundation = Depends(get_auth_foundation),
) -> UnitOfWork:
    return foundation.unit_of_work


def get_clock(
    foundation: AuthFoundation = Depends(get_auth_foundation),
) -> Clock:
    return foundation.clock


def get_user_module_facade(
    foundation: AuthFoundation = Depends(get_auth_foundation),
) -> UserModuleFacade:
    return foundation.user_facade


def get_auth_session_repository(
    foundation: AuthFoundation = Depends(get_auth_foundation),
) -> AuthSessionRepository:
    return foundation.auth_session_repository


def get_credential_repository(
    foundation: AuthFoundation = Depends(get_auth_foundation),
) -> CredentialRepository:
    return foundation.credential_repository


def get_verification_token_repository(
    foundation: AuthFoundation = Depends(get_auth_foundation),
) -> VerificationTokenRepository:
    return foundation.verification_token_repository


def get_verification_email_sender(
    foundation: AuthFoundation = Depends(get_auth_foundation),
) -> VerificationEmailSender:
    return foundation.verification_email_sender


def get_password_hasher(
    foundation: AuthFoundation = Depends(get_auth_foundation),
) -> PasswordHasher:
    return foundation.password_hasher


def get_token_service(
    foundation: AuthFoundation = Depends(get_auth_foundation),
) -> TokenService:
    return foundation.token_service


def get_lockout_policy(
    foundation: AuthFoundation = Depends(get_auth_foundation),
) -> LockoutPolicy:
    return foundation.lockout_policy


def get_password_policy(
    foundation: AuthFoundation = Depends(get_auth_foundation),
) -> PasswordPolicy:
    return foundation.password_policy


def get_reauthentication_policy(
    foundation: AuthFoundation = Depends(get_auth_foundation),
) -> ReauthenticationPolicy:
    return foundation.reauthentication_policy


def get_session_expiry_policy(
    foundation: AuthFoundation = Depends(get_auth_foundation),
) -> SessionExpiryPolicy:
    return foundation.session_expiry_policy


def get_verification_token_policy(
    foundation: AuthFoundation = Depends(get_auth_foundation),
) -> VerificationTokenPolicy:
    return foundation.verification_token_policy


def get_mfa_challenge_store(request: Request) -> MfaChallengeStore:
    store = getattr(request.app.state, "auth_mfa_challenge_store", None)
    if store is None:
        raise RuntimeError("MFA challenge store has not been configured")
    return store


def get_oidc_transaction_store(request: Request) -> OidcTransactionStore:
    store = getattr(request.app.state, "auth_oidc_transaction_store", None)
    if store is None:
        raise RuntimeError("OIDC transaction store has not been configured")
    return store


def get_auth_frontend_redirect_url() -> str:
    if not settings.AUTH_FRONTEND_REDIRECT_URL:
        raise RuntimeError("AUTH_FRONTEND_REDIRECT_URL has not been configured")
    return settings.AUTH_FRONTEND_REDIRECT_URL


def get_auth_policy_resolver(
    foundation: AuthFoundation = Depends(get_auth_foundation),
) -> AuthPolicyResolver:
    return foundation.auth_policy_resolver


def get_authentication_context_guard(
    foundation: AuthFoundation = Depends(get_auth_foundation),
) -> AuthenticationContextGuard:
    return foundation.authentication_context_guard
