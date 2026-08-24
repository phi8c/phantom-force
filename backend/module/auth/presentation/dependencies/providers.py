from __future__ import annotations

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.unit_of_work.unit_of_work import (
    UnitOfWork,
)
from app.infrastructure.persistence.session import (
    get_session,
)
from app.infrastructure.persistence.unit_of_work import (
    SqlAlchemyUnitOfWork,
)

from module.auth.domain.contracts.auth_session_repository import (
    AuthSessionRepository,
)
from module.auth.domain.contracts.clock import (
    Clock,
)
from module.auth.domain.contracts.credential_repository import (
    CredentialRepository,
)
from module.auth.domain.contracts.password_hasher import (
    PasswordHasher,
)
from module.auth.domain.contracts.token_service import (
    TokenService,
)
from module.auth.domain.contracts.lockout_policy import (
    LockoutPolicy,
)
from module.auth.domain.services.password_policy import (
    PasswordPolicy,
)
from module.auth.domain.services.session_expiry_policy import (
    SessionExpiryPolicy,
)
from module.auth.domain.services.verification_token_policy import (
    VerificationTokenPolicy,
)
from module.auth.domain.contracts.system_clock import (
    SystemClock,
)
from module.auth.infrastructure.persistence.repositories.auth_session_repository_impl import (
    AuthSessionRepositoryImpl,
)
from module.auth.infrastructure.persistence.repositories.credential_repository_impl import (
    CredentialRepositoryImpl,
)
from module.auth.infrastructure.security.argon2_password_hasher import (
    Argon2idPasswordHasher,
)
from module.auth.infrastructure.security.secure_token_service import (
    SecureTokenService,
)

from module.user.facade.contract import (
    UserModuleFacade,
)
from module.user.facade.factory import (
    get_user_facade,
)


def get_unit_of_work(
    session: AsyncSession = Depends(
        get_session,
    ),
) -> UnitOfWork:

    return SqlAlchemyUnitOfWork(
        session=session,
    )


def get_clock() -> Clock:

    return SystemClock()


def get_token_service() -> TokenService:

    return SecureTokenService()


def get_password_hasher() -> PasswordHasher:

    return Argon2idPasswordHasher()


def get_lockout_policy() -> LockoutPolicy:

    return LockoutPolicy()


def get_password_policy() -> PasswordPolicy:

    return PasswordPolicy()


def get_session_expiry_policy() -> SessionExpiryPolicy:

    return SessionExpiryPolicy()


def get_verification_token_policy() -> VerificationTokenPolicy:

    return VerificationTokenPolicy()


def get_user_module_facade(
    session: AsyncSession = Depends(
        get_session,
    ),
) -> UserModuleFacade:

    # mode="local" hardcode tam - se doc tu settings khi tach microservice
    # that, khong sua code goi noi, chi sua ham nay.
    return get_user_facade(
        mode="local",
        session=session,
    )


def get_auth_session_repository(
    session: AsyncSession = Depends(
        get_session,
    ),
) -> AuthSessionRepository:

    return AuthSessionRepositoryImpl(
        session=session,
    )


def get_credential_repository(
    session: AsyncSession = Depends(
        get_session,
    ),
) -> CredentialRepository:

    return CredentialRepositoryImpl(
        session=session,
    )