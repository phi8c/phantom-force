from __future__ import annotations

from uuid import UUID

from fastapi import Depends
from fastapi import HTTPException
from fastapi import Request
from fastapi import status

from module.auth.domain.contracts.unit_of_work import (
    UnitOfWork,
)

from module.auth.application.use_cases.resolve_current_user import (
    ResolveCurrentUserRequest,
    ResolveCurrentUserResult,
    ResolveCurrentUserUseCase,
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
    InvalidAuthenticationContextError,
    KnowledgeSpaceContextMismatchError,
    SessionExpiredError,
    SessionInvalidError,
)
from module.auth.application.services.authentication_context_guard import (
    AuthenticationContextGuard,
)
from module.auth.domain.services.session_expiry_policy import (
    SessionExpiryPolicy,
)

from module.user.facade.contract import (
    UserModuleFacade,
)

from .providers import (
    get_auth_session_repository,
    get_authentication_context_guard,
    get_clock,
    get_session_expiry_policy,
    get_token_service,
    get_unit_of_work,
    get_user_module_facade,
)

SESSION_COOKIE_NAME = "__Host-session"


def get_resolve_current_user_use_case(
    uow: UnitOfWork = Depends(
        get_unit_of_work,
    ),
    clock: Clock = Depends(
        get_clock,
    ),
    user_facade: UserModuleFacade = Depends(
        get_user_module_facade,
    ),
    auth_session_repository: AuthSessionRepository = Depends(
        get_auth_session_repository,
    ),
    token_service: TokenService = Depends(
        get_token_service,
    ),
    session_expiry_policy: SessionExpiryPolicy = Depends(
        get_session_expiry_policy,
    ),
) -> ResolveCurrentUserUseCase:

    return ResolveCurrentUserUseCase(
        uow=uow,
        clock=clock,
        user_facade=user_facade,
        auth_session_repository=auth_session_repository,
        token_service=token_service,
        session_expiry_policy=session_expiry_policy,
    )


async def get_current_user(
    request: Request,
    use_case: ResolveCurrentUserUseCase = Depends(
        get_resolve_current_user_use_case,
    ),
) -> ResolveCurrentUserResult:
    """
    Dependency chinh dung o moi endpoint can dang nhap:
    current_user: ResolveCurrentUserResult = Depends(get_current_user)
    """

    raw_token = request.cookies.get(
        SESSION_COOKIE_NAME,
    )

    if raw_token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    try:
        return await use_case.execute(
            ResolveCurrentUserRequest(
                raw_session_token=raw_token,
            ),
        )
    except (SessionInvalidError, SessionExpiredError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session invalid or expired",
        )


def require_management_user(
    current_user: ResolveCurrentUserResult = Depends(get_current_user),
    guard: AuthenticationContextGuard = Depends(get_authentication_context_guard),
) -> ResolveCurrentUserResult:
    try:
        guard.require_management(current_user)
    except InvalidAuthenticationContextError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Management authentication context is required",
        )
    return current_user


def require_knowledge_space_user(
    knowledge_space_id: UUID,
    current_user: ResolveCurrentUserResult = Depends(get_current_user),
    guard: AuthenticationContextGuard = Depends(get_authentication_context_guard),
) -> ResolveCurrentUserResult:
    enforce_knowledge_space_access(current_user, knowledge_space_id, guard)
    return current_user


def enforce_knowledge_space_access(
    current_user: ResolveCurrentUserResult,
    knowledge_space_id: UUID,
    guard: AuthenticationContextGuard,
) -> None:
    try:
        guard.require_knowledge_space(current_user, knowledge_space_id)
    except (InvalidAuthenticationContextError, KnowledgeSpaceContextMismatchError):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Knowledge Space authentication context is required",
        )
