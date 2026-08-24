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
from module.auth.domain.contracts.token_service import (
    TokenService,
)
from module.auth.domain.exception.exceptions import (
    SessionExpiredError,
    SessionInvalidError,
)
from module.auth.domain.services.session_expiry_policy import (
    SessionExpiryPolicy,
)

from module.user.facade.contract import (
    UserModuleFacade,
)

from module.auth.application.dto.request.resolve_current_user_request import ResolveCurrentUserRequest
from module.auth.application.dto.response.resolve_current_user_response import ResolveCurrentUserResult

LAST_SEEN_UPDATE_THRESHOLD_SECONDS = 60








class ResolveCurrentUserUseCase:
    """
    Day la nen tang cua get_current_user() dependency - moi request can
    dang nhap deu di qua use case nay. KHONG bao gio tin session hop le
    chi vi request co cookie - luon verify hash + revoked_at + 2 lop
    timeout doc lap (idle/absolute).
    """

    def __init__(
        self,
        uow: UnitOfWork,
        clock: Clock,
        user_facade: UserModuleFacade,
        auth_session_repository: AuthSessionRepository,
        token_service: TokenService,
        session_expiry_policy: SessionExpiryPolicy,
    ):
        self._uow = uow
        self._clock = clock
        self._user_facade = user_facade
        self._auth_sessions = auth_session_repository
        self._token_service = token_service
        self._session_expiry_policy = session_expiry_policy

    async def execute(
        self,
        request: ResolveCurrentUserRequest,
    ) -> ResolveCurrentUserResult:

        token_hash = self._token_service.hash(
            request.raw_session_token,
        )

        session = await self._auth_sessions.get_by_token_hash(
            token_hash,
        )

        if session is None:
            raise SessionInvalidError()

        if session.revoked_at is not None:
            raise SessionInvalidError()

        now = self._clock.now()

        if session.absolute_expires_at <= now:

            async with self._uow:
                session.revoked_at = now
                session.revoked_reason = "absolute_timeout"
                await self._auth_sessions.update(
                    session,
                )
                await self._uow.commit()

            raise SessionExpiredError()

        if session.idle_expires_at <= now:

            async with self._uow:
                session.revoked_at = now
                session.revoked_reason = "idle_timeout"
                await self._auth_sessions.update(
                    session,
                )
                await self._uow.commit()

            raise SessionExpiredError()

        user_dto = await self._user_facade.get_user(
            session.user_id,
        )

        if user_dto is None or user_dto.status != "active":
            raise SessionInvalidError()

        # Sliding window: chi ghi lai khi da qua nguong throttle, tranh
        # write storm moi request (vd load lien tuc 1 trang chat).
        seconds_since_last_seen = (
            now - session.last_seen_at
        ).total_seconds()

        if seconds_since_last_seen > LAST_SEEN_UPDATE_THRESHOLD_SECONDS:

            async with self._uow:
                session.last_seen_at = now
                session.idle_expires_at = (
                    self._session_expiry_policy.compute_idle_expiry(
                        now,
                    )
                )
                await self._auth_sessions.update(
                    session,
                )
                await self._uow.commit()

        return ResolveCurrentUserResult(
            user_id=user_dto.id,
            email=user_dto.email,
            session_id=session.id,
        )