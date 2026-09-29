from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from module.auth.application.services.auth_policy_resolver import AuthPolicyResolver
from module.auth.application.services.authentication_context_guard import (
    AuthenticationContextGuard,
)
from module.auth.application.services.local_authentication_service import (
    LocalAuthenticationService,
)
from module.auth.application.services.entra_authentication_service import (
    EntraAuthenticationService,
)
from module.auth.application.services.oidc_authentication_service import (
    OidcAuthenticationService,
)
from module.auth.application.services.security_audit_service import SecurityAuditService
from module.auth.domain.contracts.auth_session_repository import AuthSessionRepository
from module.auth.domain.contracts.clock import Clock
from module.auth.domain.contracts.credential_repository import CredentialRepository
from module.auth.domain.contracts.identity_link_repository import IdentityLinkRepository
from module.auth.domain.contracts.knowledge_space_auth_policy_repository import (
    KnowledgeSpaceAuthPolicyRepository,
)
from module.auth.domain.contracts.management_auth_policy_repository import (
    ManagementAuthPolicyRepository,
)
from module.auth.domain.contracts.mfa_challenge_store import MfaChallengeStore
from module.auth.domain.contracts.mfa_provider import MfaProvider
from module.auth.domain.contracts.encryptor import Encryptor
from module.auth.domain.contracts.oidc_provider import OidcProvider
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
from module.auth.domain.contracts.system_clock import SystemClock
from module.auth.domain.services.password_policy import PasswordPolicy
from module.auth.domain.services.reauthentication_policy import ReauthenticationPolicy
from module.auth.domain.services.mfa_policy import MfaPolicy
from module.auth.domain.services.session_expiry_policy import SessionExpiryPolicy
from module.auth.domain.services.verification_token_policy import VerificationTokenPolicy
from module.auth.domain.contracts.lockout_policy import LockoutPolicy
from module.auth.infrastructure.persistence.repositories.auth_session_repository_impl import (
    AuthSessionRepositoryImpl,
)
from module.auth.infrastructure.persistence.repositories.credential_repository_impl import (
    CredentialRepositoryImpl,
)
from module.auth.infrastructure.persistence.repositories.identity_link_repository_impl import (
    IdentityLinkRepositoryImpl,
)
from module.auth.infrastructure.persistence.repositories.knowledge_space_auth_policy_repository_impl import (
    KnowledgeSpaceAuthPolicyRepositoryImpl,
)
from module.auth.infrastructure.persistence.repositories.management_auth_policy_repository_impl import (
    ManagementAuthPolicyRepositoryImpl,
)
from module.auth.infrastructure.persistence.repositories.security_audit_repository_impl import (
    SecurityAuditRepositoryImpl,
)
from module.auth.infrastructure.persistence.repositories.verification_token_repository_impl import (
    VerificationTokenRepositoryImpl,
)
from module.auth.infrastructure.persistence.sqlalchemy_unit_of_work import (
    SqlAlchemyUnitOfWork,
)
from module.auth.infrastructure.email.smtp_verification_email_sender import (
    SmtpVerificationEmailSender,
)
from module.auth.infrastructure.mfa.totp_provider import TotpMfaProvider
from module.auth.infrastructure.oidc.microsoft_entra_oidc_provider import (
    MicrosoftEntraOidcProvider,
)
from module.auth.infrastructure.security.fernet_encryptor import FernetEncryptor
from module.auth.infrastructure.security.argon2_password_hasher import (
    Argon2idPasswordHasher,
)
from module.auth.infrastructure.security.secure_token_service import SecureTokenService
from module.user.facade.contract import UserModuleFacade
from module.user.facade.factory import get_user_facade
from module.knowledge_space.facade.contract import KnowledgeSpaceModuleFacade
from module.knowledge_space.facade.factory import get_knowledge_space_facade
from shared.config.settings import settings


@dataclass(frozen=True)
class AuthFoundation:
    unit_of_work: UnitOfWork
    clock: Clock
    user_facade: UserModuleFacade
    knowledge_space_facade: KnowledgeSpaceModuleFacade
    auth_session_repository: AuthSessionRepository
    identity_link_repository: IdentityLinkRepository
    credential_repository: CredentialRepository
    verification_token_repository: VerificationTokenRepository
    verification_email_sender: VerificationEmailSender
    knowledge_space_auth_policy_repository: KnowledgeSpaceAuthPolicyRepository
    management_auth_policy_repository: ManagementAuthPolicyRepository
    password_hasher: PasswordHasher
    token_service: TokenService
    lockout_policy: LockoutPolicy
    password_policy: PasswordPolicy
    reauthentication_policy: ReauthenticationPolicy
    session_expiry_policy: SessionExpiryPolicy
    verification_token_policy: VerificationTokenPolicy
    mfa_policy: MfaPolicy
    mfa_provider: MfaProvider
    encryptor: Encryptor
    oidc_provider: OidcProvider
    auth_policy_resolver: AuthPolicyResolver
    authentication_context_guard: AuthenticationContextGuard
    security_audit: SecurityAuditService


def create_auth_foundation(session: AsyncSession) -> AuthFoundation:
    clock = SystemClock()
    knowledge_space_facade = get_knowledge_space_facade(session=session)
    knowledge_space_policy_repository = KnowledgeSpaceAuthPolicyRepositoryImpl(
        session=session
    )
    management_policy_repository = ManagementAuthPolicyRepositoryImpl(
        session=session
    )

    return AuthFoundation(
        unit_of_work=SqlAlchemyUnitOfWork(session),
        clock=clock,
        user_facade=get_user_facade(mode="local", session=session),
        knowledge_space_facade=knowledge_space_facade,
        auth_session_repository=AuthSessionRepositoryImpl(session=session),
        identity_link_repository=IdentityLinkRepositoryImpl(session=session),
        credential_repository=CredentialRepositoryImpl(session=session),
        verification_token_repository=VerificationTokenRepositoryImpl(session=session),
        verification_email_sender=SmtpVerificationEmailSender(
            host=settings.SMTP_HOST,
            port=settings.SMTP_PORT,
            username=settings.SMTP_USERNAME,
            password=settings.SMTP_PASSWORD,
            sender=settings.SMTP_FROM_EMAIL,
            verification_url=settings.AUTH_VERIFICATION_URL,
            use_tls=settings.SMTP_USE_TLS,
        ),
        knowledge_space_auth_policy_repository=knowledge_space_policy_repository,
        management_auth_policy_repository=management_policy_repository,
        password_hasher=Argon2idPasswordHasher(),
        token_service=SecureTokenService(),
        lockout_policy=LockoutPolicy(),
        password_policy=PasswordPolicy(),
        reauthentication_policy=ReauthenticationPolicy(),
        session_expiry_policy=SessionExpiryPolicy(),
        verification_token_policy=VerificationTokenPolicy(),
        mfa_policy=MfaPolicy(),
        mfa_provider=TotpMfaProvider(issuer=settings.AUTH_MFA_ISSUER),
        encryptor=FernetEncryptor(key=settings.AUTH_MFA_ENCRYPTION_KEY),
        oidc_provider=MicrosoftEntraOidcProvider(
            client_id=settings.ENTRA_CLIENT_ID,
            client_secret=settings.ENTRA_CLIENT_SECRET,
            redirect_uri=settings.ENTRA_REDIRECT_URI,
        ),
        auth_policy_resolver=AuthPolicyResolver(
            management_policy_repository=management_policy_repository,
            knowledge_space_policy_repository=knowledge_space_policy_repository,
            knowledge_space_facade=knowledge_space_facade,
        ),
        authentication_context_guard=AuthenticationContextGuard(),
        security_audit=SecurityAuditService(
            repository=SecurityAuditRepositoryImpl(session),
            clock=clock,
        ),
    )


def create_local_authentication_service(
    foundation: AuthFoundation,
    mfa_challenge_store: MfaChallengeStore,
) -> LocalAuthenticationService:
    return LocalAuthenticationService(
        uow=foundation.unit_of_work,
        clock=foundation.clock,
        user_facade=foundation.user_facade,
        credential_repository=foundation.credential_repository,
        auth_session_repository=foundation.auth_session_repository,
        mfa_challenge_store=mfa_challenge_store,
        password_hasher=foundation.password_hasher,
        token_service=foundation.token_service,
        lockout_policy=foundation.lockout_policy,
        session_expiry_policy=foundation.session_expiry_policy,
        mfa_policy=foundation.mfa_policy,
        security_audit=foundation.security_audit,
    )


def create_oidc_authentication_service(
    foundation: AuthFoundation,
    transaction_store: OidcTransactionStore,
) -> OidcAuthenticationService:
    return OidcAuthenticationService(
        clock=foundation.clock,
        provider=foundation.oidc_provider,
        transaction_store=transaction_store,
    )


def create_entra_authentication_service(
    foundation: AuthFoundation,
    mfa_challenge_store: MfaChallengeStore,
) -> EntraAuthenticationService:
    return EntraAuthenticationService(
        uow=foundation.unit_of_work,
        clock=foundation.clock,
        users=foundation.user_facade,
        identity_links=foundation.identity_link_repository,
        credentials=foundation.credential_repository,
        sessions=foundation.auth_session_repository,
        mfa_challenges=mfa_challenge_store,
        tokens=foundation.token_service,
        session_expiry=foundation.session_expiry_policy,
        mfa=foundation.mfa_policy,
        security_audit=foundation.security_audit,
    )
