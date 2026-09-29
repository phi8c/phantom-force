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

from module.auth.application.dto.request.logout_all_sessions_request import LogoutAllSessionsRequest
from module.auth.application.services.security_audit_service import SecurityAuditService





class LogoutAllSessionsUseCase:
    """
    Dung khi user nghi ngo bi chiem tai khoan, hoac ngay sau khi doi
    password (buoc bat buoc theo thiet ke tu dau - doi password phai
    revoke toan bo session dang hoat dong).
    """

    def __init__(
        self,
        uow: UnitOfWork,
        clock: Clock,
        auth_session_repository: AuthSessionRepository,
        security_audit: SecurityAuditService | None = None,
    ):
        self._uow = uow
        self._clock = clock
        self._auth_sessions = auth_session_repository
        self._audit = security_audit

    async def execute(
        self,
        request: LogoutAllSessionsRequest,
    ) -> None:

        async with self._uow:

            await self._auth_sessions.revoke_all_by_user_id(
                request.user_id,
                self._clock.now(),
                request.reason,
            )
            if self._audit is not None:
                await self._audit.record(
                    "auth.session.logout_all",
                    actor_user_id=request.user_id,
                    target_type="user",
                    target_id=request.user_id,
                )

            await self._uow.commit()
