from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from app.domain.unit_of_work.unit_of_work import (
    UnitOfWork,
)

from module.auth.domain.contracts.auth_session_repository import (
    AuthSessionRepository,
)
from module.auth.domain.contracts.clock import (
    Clock,
)

from module.auth.application.dto.request.logout_all_sessions_request import LogoutAllSessionsRequest





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
    ):
        self._uow = uow
        self._clock = clock
        self._auth_sessions = auth_session_repository

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

            await self._uow.commit()