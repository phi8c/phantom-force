from __future__ import annotations

from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import Request
from fastapi import Response
from fastapi import status

from module.auth.application.use_cases.local_login import (
    LocalLoginRequest,
    LocalLoginUseCase,
)
from module.auth.application.use_cases.logout import (
    LogoutRequest,
    LogoutUseCase,
)
from module.auth.application.use_cases.register_local_user import (
    RegisterLocalUserRequest,
    RegisterLocalUserUseCase,
)
from module.auth.domain.exception.exceptions import (
    AccountLockedError,
    InvalidCredentialsError,
    WeakPasswordError,
)

from ..dependencies.auth_dependencies import (
    SESSION_COOKIE_NAME,
    get_current_user,
)
from ..dependencies.use_case_providers import (
    get_local_login_use_case,
    get_logout_use_case,
    get_register_local_user_use_case,
)
from ..schemas.auth_schema import (
    CurrentUserSchema,
    LocalLoginResponseSchema,
    LocalLoginSchema,
    RegisterLocalUserResponseSchema,
    RegisterLocalUserSchema,
)

router = APIRouter(
    prefix="/auth",
    tags=[
        "auth",
    ],
)


@router.post(
    "/register",
    response_model=RegisterLocalUserResponseSchema,
)
async def register_local_user(
    body: RegisterLocalUserSchema,
    use_case: RegisterLocalUserUseCase = Depends(
        get_register_local_user_use_case,
    ),
) -> RegisterLocalUserResponseSchema:

    try:
        result = await use_case.execute(
            RegisterLocalUserRequest(
                email=body.email,
                password=body.password,
            ),
        )
    except WeakPasswordError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )

    # TODO: goi email service gui result.raw_verification_token qua email -
    # chua lam, se lam khi co infra gui mail. KHONG bao gio tra token nay
    # trong response.

    return RegisterLocalUserResponseSchema(
        message=result.message,
    )


@router.post(
    "/login/local",
    response_model=LocalLoginResponseSchema,
)
async def login_local(
    body: LocalLoginSchema,
    request: Request,
    response: Response,
    use_case: LocalLoginUseCase = Depends(
        get_local_login_use_case,
    ),
) -> LocalLoginResponseSchema:

    try:
        result = await use_case.execute(
            LocalLoginRequest(
                email=body.email,
                password=body.password,
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get(
                    "user-agent",
                ),
                device_fingerprint=request.headers.get(
                    "x-device-fingerprint",
                ),
            ),
        )
    except InvalidCredentialsError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email hoac password khong dung",
        )
    except AccountLockedError as exc:
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail=f"Tai khoan tam khoa den {exc.locked_until.isoformat()}",
        )

    if result.status == "success":

        response.set_cookie(
            key=SESSION_COOKIE_NAME,
            value=result.session_token,
            httponly=True,
            secure=True,
            samesite="strict",
            path="/",
        )

    return LocalLoginResponseSchema(
        status=result.status,
        mfa_challenge_id=result.mfa_challenge_id,
    )


@router.post(
    "/logout",
)
async def logout(
    request: Request,
    response: Response,
    use_case: LogoutUseCase = Depends(
        get_logout_use_case,
    ),
) -> dict[str, bool]:

    raw_token = request.cookies.get(
        SESSION_COOKIE_NAME,
    )

    if raw_token is not None:
        await use_case.execute(
            LogoutRequest(
                raw_session_token=raw_token,
            ),
        )

    response.delete_cookie(
        key=SESSION_COOKIE_NAME,
        path="/",
        samesite="strict",
    )

    return {
        "success": True,
    }


@router.get(
    "/me",
    response_model=CurrentUserSchema,
)
async def get_me(
    current_user=Depends(
        get_current_user,
    ),
) -> CurrentUserSchema:

    return CurrentUserSchema(
        user_id=str(
            current_user.user_id,
        ),
        email=current_user.email,
    )