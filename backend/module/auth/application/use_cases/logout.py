from __future__ import annotations

from dataclasses import dataclass

from app.domain.unit_of_work.unit_of_work import (
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
    ):
        self._uow = uow
        self._clock = clock
        self._token_service = token_service
        self._auth_sessions = auth_session_repository

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

            await self._uow.commit()