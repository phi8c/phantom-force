from __future__ import annotations

from module.auth.domain.contracts.unit_of_work import (
    UnitOfWork,
)

from module.auth.domain.contracts.auth_session_repository import (
    AuthSessionRepository,
)
from module.auth.domain.contracts.clock import (
    Clock,
)
from module.auth.domain.contracts.token_service import (
    TokenService,
)
from module.auth.application.dto.request.logout_request import LogoutRequest
from module.auth.application.services.security_audit_service import SecurityAuditService





class LogoutUseCase:
    """
    Idempotent co chu dich: goi logout voi token da revoke roi (double-click,
    request lap) khong raise loi - luon tra ve thanh cong, khong tiet lo
    session co ton tai hay khong cho client.
    """

    def __init__(
        self,
        uow: UnitOfWork,
        clock: Clock,
        token_service: TokenService,
        auth_session_repository: AuthSessionRepository,
        security_audit: SecurityAuditService | None = None,
    ):
        self._uow = uow
        self._clock = clock
        self._token_service = token_service
        self._auth_sessions = auth_session_repository
        self._audit = security_audit

    async def execute(
        self,
        request: LogoutRequest,
    ) -> None:

        token_hash = self._token_service.hash(
            request.raw_session_token,
        )

        session = await self._auth_sessions.get_by_token_hash(
            token_hash,
        )

        if session is None or session.revoked_at is not None:
            return

        async with self._uow:

            session.revoked_at = self._clock.now()
            session.revoked_reason = "user_logout"

            await self._auth_sessions.update(
                session,
            )
            if self._audit is not None:
                await self._audit.record(
                    "auth.session.logout",
                    actor_user_id=session.user_id,
                    target_type="auth_session",
                    target_id=session.id,
                )

            await self._uow.commit()
