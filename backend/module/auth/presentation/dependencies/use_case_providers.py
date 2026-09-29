from __future__ import annotations

from fastapi import Depends

from module.auth.application.use_cases.knowledge_space_local_login import (
    KnowledgeSpaceLocalLoginUseCase,
)
from module.auth.application.use_cases.management_local_login import (
    ManagementLocalLoginUseCase,
)
from module.auth.application.use_cases.logout import LogoutUseCase
from module.auth.application.use_cases.logout_all_session import LogoutAllSessionsUseCase
from module.auth.application.use_cases.register_local_user import RegisterLocalUserUseCase
from module.auth.application.use_cases.verify_email import VerifyEmailUseCase
from module.auth.application.use_cases.verify_mfa import VerifyMfaUseCase
from module.auth.application.use_cases.complete_oidc import CompleteOidcUseCase
from module.auth.application.use_cases.get_knowledge_space_auth_requirement import (
    GetKnowledgeSpaceAuthRequirementUseCase,
)
from module.auth.application.use_cases.knowledge_space_oidc_start import (
    KnowledgeSpaceOidcStartUseCase,
)
from module.auth.application.use_cases.management_oidc_start import (
    ManagementOidcStartUseCase,
)
from module.auth.domain.contracts.auth_session_repository import AuthSessionRepository
from module.auth.domain.contracts.clock import Clock
from module.auth.domain.contracts.credential_repository import CredentialRepository
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
from module.auth.domain.services.verification_token_policy import VerificationTokenPolicy
from module.auth.composition.factory import (
    AuthFoundation,
    create_entra_authentication_service,
    create_local_authentication_service,
    create_oidc_authentication_service,
)
from module.user.facade.contract import UserModuleFacade

from .providers import (
    get_auth_session_repository,
    get_auth_foundation,
    get_clock,
    get_credential_repository,
    get_mfa_challenge_store,
    get_oidc_transaction_store,
    get_password_hasher,
    get_password_policy,
    get_token_service,
    get_unit_of_work,
    get_user_module_facade,
    get_verification_token_policy,
    get_verification_token_repository,
    get_verification_email_sender,
)


def get_register_local_user_use_case(
    uow: UnitOfWork = Depends(get_unit_of_work),
    clock: Clock = Depends(get_clock),
    user_facade: UserModuleFacade = Depends(get_user_module_facade),
    credential_repository: CredentialRepository = Depends(get_credential_repository),
    verification_token_repository: VerificationTokenRepository = Depends(
        get_verification_token_repository
    ),
    password_hasher: PasswordHasher = Depends(get_password_hasher),
    password_policy: PasswordPolicy = Depends(get_password_policy),
    verification_token_policy: VerificationTokenPolicy = Depends(
        get_verification_token_policy
    ),
    token_service: TokenService = Depends(get_token_service),
    verification_email_sender: VerificationEmailSender = Depends(
        get_verification_email_sender
    ),
    foundation: AuthFoundation = Depends(get_auth_foundation),
) -> RegisterLocalUserUseCase:
    return RegisterLocalUserUseCase(
        uow=uow,
        clock=clock,
        user_facade=user_facade,
        credential_repository=credential_repository,
        verification_token_repository=verification_token_repository,
        password_hasher=password_hasher,
        password_policy=password_policy,
        verification_token_policy=verification_token_policy,
        token_service=token_service,
        verification_email_sender=verification_email_sender,
        security_audit=foundation.security_audit,
    )


def get_verify_email_use_case(
    uow: UnitOfWork = Depends(get_unit_of_work),
    clock: Clock = Depends(get_clock),
    user_facade: UserModuleFacade = Depends(get_user_module_facade),
    verification_token_repository: VerificationTokenRepository = Depends(
        get_verification_token_repository
    ),
    token_service: TokenService = Depends(get_token_service),
    foundation: AuthFoundation = Depends(get_auth_foundation),
) -> VerifyEmailUseCase:
    return VerifyEmailUseCase(
        uow=uow,
        clock=clock,
        user_facade=user_facade,
        verification_token_repository=verification_token_repository,
        token_service=token_service,
        security_audit=foundation.security_audit,
    )


def get_management_local_login_use_case(
    foundation: AuthFoundation = Depends(get_auth_foundation),
    mfa_challenge_store: MfaChallengeStore = Depends(get_mfa_challenge_store),
) -> ManagementLocalLoginUseCase:
    return ManagementLocalLoginUseCase(
        policy_resolver=foundation.auth_policy_resolver,
        local_authentication=create_local_authentication_service(
            foundation,
            mfa_challenge_store,
        ),
    )


def get_knowledge_space_local_login_use_case(
    foundation: AuthFoundation = Depends(get_auth_foundation),
    mfa_challenge_store: MfaChallengeStore = Depends(get_mfa_challenge_store),
) -> KnowledgeSpaceLocalLoginUseCase:
    return KnowledgeSpaceLocalLoginUseCase(
        policy_resolver=foundation.auth_policy_resolver,
        local_authentication=create_local_authentication_service(
            foundation,
            mfa_challenge_store,
        ),
    )


def get_verify_mfa_use_case(
    foundation: AuthFoundation = Depends(get_auth_foundation),
    mfa_challenge_store: MfaChallengeStore = Depends(get_mfa_challenge_store),
) -> VerifyMfaUseCase:
    return VerifyMfaUseCase(
        uow=foundation.unit_of_work,
        clock=foundation.clock,
        user_facade=foundation.user_facade,
        credential_repository=foundation.credential_repository,
        auth_session_repository=foundation.auth_session_repository,
        challenge_store=mfa_challenge_store,
        mfa_provider=foundation.mfa_provider,
        encryptor=foundation.encryptor,
        token_service=foundation.token_service,
        session_expiry_policy=foundation.session_expiry_policy,
        security_audit=foundation.security_audit,
    )


def get_management_oidc_start_use_case(
    foundation: AuthFoundation = Depends(get_auth_foundation),
    transaction_store: OidcTransactionStore = Depends(get_oidc_transaction_store),
) -> ManagementOidcStartUseCase:
    return ManagementOidcStartUseCase(
        policies=foundation.auth_policy_resolver,
        oidc=create_oidc_authentication_service(foundation, transaction_store),
    )


def get_knowledge_space_oidc_start_use_case(
    foundation: AuthFoundation = Depends(get_auth_foundation),
    transaction_store: OidcTransactionStore = Depends(get_oidc_transaction_store),
) -> KnowledgeSpaceOidcStartUseCase:
    return KnowledgeSpaceOidcStartUseCase(
        policies=foundation.auth_policy_resolver,
        oidc=create_oidc_authentication_service(foundation, transaction_store),
    )


def get_knowledge_space_auth_requirement_use_case(
    foundation: AuthFoundation = Depends(get_auth_foundation),
) -> GetKnowledgeSpaceAuthRequirementUseCase:
    return GetKnowledgeSpaceAuthRequirementUseCase(
        policy_resolver=foundation.auth_policy_resolver,
    )


def get_complete_oidc_use_case(
    foundation: AuthFoundation = Depends(get_auth_foundation),
    transaction_store: OidcTransactionStore = Depends(get_oidc_transaction_store),
    mfa_challenge_store: MfaChallengeStore = Depends(get_mfa_challenge_store),
) -> CompleteOidcUseCase:
    return CompleteOidcUseCase(
        oidc=create_oidc_authentication_service(foundation, transaction_store),
        entra_authentication=create_entra_authentication_service(
            foundation,
            mfa_challenge_store,
        ),
    )


def get_logout_use_case(
    foundation: AuthFoundation = Depends(get_auth_foundation),
    uow: UnitOfWork = Depends(get_unit_of_work),
    clock: Clock = Depends(get_clock),
    token_service: TokenService = Depends(get_token_service),
    auth_session_repository: AuthSessionRepository = Depends(
        get_auth_session_repository
    ),
) -> LogoutUseCase:
    return LogoutUseCase(
        uow=uow,
        clock=clock,
        token_service=token_service,
        auth_session_repository=auth_session_repository,
        security_audit=foundation.security_audit,
    )


def get_logout_all_sessions_use_case(
    foundation: AuthFoundation = Depends(get_auth_foundation),
    uow: UnitOfWork = Depends(get_unit_of_work),
    clock: Clock = Depends(get_clock),
    auth_session_repository: AuthSessionRepository = Depends(
        get_auth_session_repository
    ),
) -> LogoutAllSessionsUseCase:
    return LogoutAllSessionsUseCase(
        uow=uow,
        clock=clock,
        auth_session_repository=auth_session_repository,
        security_audit=foundation.security_audit,
    )
