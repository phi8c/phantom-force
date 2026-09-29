from uuid import uuid4

from module.auth.application.dto.response.local_login_response import LocalLoginResult
from module.auth.application.dto.response.verified_oidc_authentication import (
    VerifiedOidcAuthentication,
)
from module.auth.application.services.security_audit_service import SecurityAuditService
from module.auth.domain.contracts.auth_session_repository import AuthSessionRepository
from module.auth.domain.contracts.clock import Clock
from module.auth.domain.contracts.credential_repository import CredentialRepository
from module.auth.domain.contracts.identity_link_repository import IdentityLinkRepository
from module.auth.domain.contracts.mfa_challenge_store import MfaChallengeStore
from module.auth.domain.contracts.token_service import TokenService
from module.auth.domain.contracts.unit_of_work import UnitOfWork
from module.auth.domain.entities.auth_session import AuthSession
from module.auth.domain.entities.identity_link import IdentityLink
from module.auth.domain.enums.auth_provider import AuthProvider
from module.auth.domain.exception.exceptions import (
    AccountDisabledError,
    ExplicitAccountLinkRequiredError,
    ExternalIdentityConflictError,
    OidcTenantMismatchError,
)
from module.auth.domain.services.mfa_policy import MfaPolicy
from module.auth.domain.services.session_expiry_policy import SessionExpiryPolicy
from module.auth.domain.value_objects.mfa_challenge import MfaChallenge
from module.user.facade.contract import UserModuleFacade
from module.user.facade.exceptions import UserAlreadyExistsError


class EntraAuthenticationService:
    def __init__(
        self,
        uow: UnitOfWork,
        clock: Clock,
        users: UserModuleFacade,
        identity_links: IdentityLinkRepository,
        credentials: CredentialRepository,
        sessions: AuthSessionRepository,
        mfa_challenges: MfaChallengeStore,
        tokens: TokenService,
        session_expiry: SessionExpiryPolicy,
        mfa: MfaPolicy,
        security_audit: SecurityAuditService | None = None,
    ):
        self._uow = uow
        self._clock = clock
        self._users = users
        self._identity_links = identity_links
        self._credentials = credentials
        self._sessions = sessions
        self._mfa_challenges = mfa_challenges
        self._tokens = tokens
        self._session_expiry = session_expiry
        self._mfa = mfa
        self._audit = security_audit

    async def authenticate(
        self,
        verified: VerifiedOidcAuthentication,
        *,
        ip_address: str | None,
        user_agent: str | None,
        device_fingerprint: str | None,
    ) -> LocalLoginResult:
        identity = await self._resolve_or_provision_identity(verified)
        user = await self._users.get_user(identity.user_id)
        if user is None or user.status != "active":
            raise AccountDisabledError("User account is not active")

        transaction = verified.transaction
        now = self._clock.now()
        credential = await self._credentials.get_by_user_id(user.id)
        has_mfa = bool(credential and credential.mfa_enabled)

        if self._mfa.enrollment_is_required(transaction.require_mfa, has_mfa):
            return LocalLoginResult(status="mfa_enrollment_required")

        if self._mfa.is_required(transaction.require_mfa, has_mfa):
            challenge_id = await self._mfa_challenges.create_challenge(
                MfaChallenge(
                    user_id=user.id,
                    auth_method=AuthProvider.ENTRA,
                    context_type=transaction.context_type,
                    knowledge_space_id=transaction.knowledge_space_id,
                    idle_timeout_minutes=transaction.idle_timeout_minutes,
                    absolute_timeout_minutes=transaction.absolute_timeout_minutes,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    device_fingerprint=device_fingerprint,
                    created_at=now,
                    expires_at=self._mfa.challenge_expires_at(now),
                    identity_link_id=identity.id,
                )
            )
            return LocalLoginResult(
                status="mfa_required",
                mfa_challenge_id=challenge_id,
            )

        raw_token = self._tokens.generate_raw_token()
        session = AuthSession.create(
            id=uuid4(),
            user_id=user.id,
            session_token_hash=self._tokens.hash(raw_token),
            auth_method=AuthProvider.ENTRA,
            context_type=transaction.context_type,
            knowledge_space_id=transaction.knowledge_space_id,
            identity_link_id=identity.id,
            ip_address=ip_address,
            user_agent=user_agent,
            device_fingerprint=device_fingerprint,
            now=now,
            idle_expires_at=self._session_expiry.compute_idle_expiry(
                now, transaction.idle_timeout_minutes
            ),
            absolute_expires_at=self._session_expiry.compute_absolute_expiry(
                now, transaction.absolute_timeout_minutes
            ),
        )
        async with self._uow:
            await self._sessions.add(session)
            if self._audit is not None:
                await self._audit.record(
                    "auth.session.created",
                    actor_user_id=user.id,
                    target_type="auth_session",
                    target_id=session.id,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    device_fingerprint=device_fingerprint,
                    metadata={
                        "method": "entra",
                        "context": transaction.context_type.value,
                    },
                )
            await self._uow.commit()
        return LocalLoginResult(status="success", session_token=raw_token)

    async def _resolve_or_provision_identity(
        self,
        verified: VerifiedOidcAuthentication,
    ) -> IdentityLink:
        info = verified.user_info
        existing = await self._identity_links.get_by_provider_and_sub(
            AuthProvider.ENTRA,
            info.external_sub,
        )
        if existing is not None:
            if existing.tenant_id != info.tenant_id:
                raise OidcTenantMismatchError("External identity tenant has changed")
            return existing

        # Matching email alone is not proof that two identities have one owner.
        if await self._users.get_user_by_email(info.email) is not None:
            raise ExplicitAccountLinkRequiredError(
                "An account with this email already exists and requires explicit linking"
            )

        now = self._clock.now()
        try:
            async with self._uow:
                user = await self._users.create_user(info.email)
                await self._users.activate_external_user(
                    user.id,
                    now if info.email_verified else None,
                )
                identity = await self._identity_links.add(
                    IdentityLink(
                        id=uuid4(),
                        user_id=user.id,
                        provider=AuthProvider.ENTRA,
                        external_sub=info.external_sub,
                        tenant_id=info.tenant_id,
                        email_at_link=info.email,
                        linked_at=now,
                    )
                )
                if self._audit is not None:
                    await self._audit.record(
                        "auth.identity.provisioned",
                        actor_user_id=user.id,
                        target_type="identity_link",
                        target_id=identity.id,
                        metadata={"provider": "entra"},
                    )
                await self._uow.commit()
                return identity
        except (ExternalIdentityConflictError, UserAlreadyExistsError):
            await self._uow.rollback()
            concurrent = await self._identity_links.get_by_provider_and_sub(
                AuthProvider.ENTRA,
                info.external_sub,
            )
            if concurrent is not None and concurrent.tenant_id == info.tenant_id:
                return concurrent
            raise ExplicitAccountLinkRequiredError(
                "External identity could not be provisioned safely"
            )
