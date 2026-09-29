from __future__ import annotations

from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import Request
from fastapi import Response
from fastapi import status
from fastapi.responses import RedirectResponse
from uuid import UUID

from module.auth.application.dto.request.knowledge_space_local_login_request import (
    KnowledgeSpaceLocalLoginRequest,
)
from module.auth.application.dto.request.knowledge_space_oidc_start_request import (
    KnowledgeSpaceOidcStartRequest,
)
from module.auth.application.dto.request.complete_oidc_request import CompleteOidcRequest
from module.auth.application.dto.request.management_local_login_request import (
    ManagementLocalLoginRequest,
)
from module.auth.application.dto.request.logout_request import LogoutRequest
from module.auth.application.dto.request.logout_all_sessions_request import (
    LogoutAllSessionsRequest,
)
from module.auth.application.dto.request.register_local_user_request import (
    RegisterLocalUserRequest,
)
from module.auth.application.dto.request.verify_email_request import VerifyEmailRequest
from module.auth.application.dto.request.verify_mfa_request import VerifyMfaRequest
from module.auth.application.use_cases.knowledge_space_local_login import (
    KnowledgeSpaceLocalLoginUseCase,
)
from module.auth.application.use_cases.knowledge_space_oidc_start import (
    KnowledgeSpaceOidcStartUseCase,
)
from module.auth.application.use_cases.complete_oidc import CompleteOidcUseCase
from module.auth.application.use_cases.get_knowledge_space_auth_requirement import (
    GetKnowledgeSpaceAuthRequirementUseCase,
)
from module.auth.application.use_cases.management_local_login import (
    ManagementLocalLoginUseCase,
)
from module.auth.application.use_cases.management_oidc_start import (
    ManagementOidcStartUseCase,
)
from module.auth.application.use_cases.logout import LogoutUseCase
from module.auth.application.use_cases.logout_all_session import LogoutAllSessionsUseCase
from module.auth.application.use_cases.register_local_user import RegisterLocalUserUseCase
from module.auth.application.use_cases.verify_email import VerifyEmailUseCase
from module.auth.application.use_cases.verify_mfa import VerifyMfaUseCase
from module.auth.domain.exception.exceptions import (
    AccountLockedError,
    AuthenticationMethodNotAllowedError,
    AuthenticationPolicyInactiveError,
    AuthenticationPolicyMissingError,
    AccountDisabledError,
    InvalidCredentialsError,
    InvalidMfaChallengeError,
    ExpiredVerificationTokenError,
    InvalidVerificationTokenError,
    KnowledgeSpaceNotFoundError,
    ExplicitAccountLinkRequiredError,
    OidcStateInvalidError,
    OidcTenantMismatchError,
    OidcTokenValidationError,
    OidcTransactionExpiredError,
    VerificationDeliveryError,
    WeakPasswordError,
)

from ..dependencies.auth_dependencies import (
    SESSION_COOKIE_NAME,
    get_current_user,
)
from ..dependencies.providers import get_auth_frontend_redirect_url
from ..redirects import append_auth_result
from ..dependencies.use_case_providers import (
    get_complete_oidc_use_case,
    get_knowledge_space_auth_requirement_use_case,
    get_knowledge_space_local_login_use_case,
    get_knowledge_space_oidc_start_use_case,
    get_management_local_login_use_case,
    get_management_oidc_start_use_case,
    get_logout_use_case,
    get_logout_all_sessions_use_case,
    get_register_local_user_use_case,
    get_verify_email_use_case,
    get_verify_mfa_use_case,
)
from ..schemas.auth_schema import (
    CurrentUserSchema,
    LocalLoginResponseSchema,
    LocalLoginSchema,
    KnowledgeSpaceAuthRequirementSchema,
    OidcStartResponseSchema,
    RegisterLocalUserResponseSchema,
    RegisterLocalUserSchema,
    VerifyEmailResponseSchema,
    VerifyEmailSchema,
    VerifyMfaSchema,
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
    except VerificationDeliveryError:
        return RegisterLocalUserResponseSchema(
            message="Neu email hop le, ban se nhan duoc email xac thuc.",
        )

    return RegisterLocalUserResponseSchema(
        message=result.message,
    )


@router.post(
    "/verify-email",
    response_model=VerifyEmailResponseSchema,
)
async def verify_email(
    body: VerifyEmailSchema,
    use_case: VerifyEmailUseCase = Depends(get_verify_email_use_case),
) -> VerifyEmailResponseSchema:
    try:
        result = await use_case.execute(VerifyEmailRequest(raw_token=body.token))
    except (InvalidVerificationTokenError, ExpiredVerificationTokenError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Verification token is invalid or expired",
        )
    return VerifyEmailResponseSchema(message=result.message)


@router.get(
    "/knowledge-spaces/{knowledge_space_id}/requirement",
    response_model=KnowledgeSpaceAuthRequirementSchema,
)
async def get_knowledge_space_auth_requirement(
    knowledge_space_id: UUID,
    use_case: GetKnowledgeSpaceAuthRequirementUseCase = Depends(
        get_knowledge_space_auth_requirement_use_case,
    ),
) -> KnowledgeSpaceAuthRequirementSchema:
    try:
        result = await use_case.execute(knowledge_space_id)
    except KnowledgeSpaceNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Knowledge Space not found",
        )
    except (AuthenticationPolicyMissingError, AuthenticationPolicyInactiveError):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Authentication is not available",
        )
    return KnowledgeSpaceAuthRequirementSchema(
        auth_method=result.auth_method,
        require_mfa=result.require_mfa,
    )


@router.post(
    "/management/login/local",
    response_model=LocalLoginResponseSchema,
)
async def management_login_local(
    body: LocalLoginSchema,
    request: Request,
    response: Response,
    use_case: ManagementLocalLoginUseCase = Depends(
        get_management_local_login_use_case,
    ),
) -> LocalLoginResponseSchema:
    try:
        result = await use_case.execute(
            ManagementLocalLoginRequest(
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
    except (InvalidCredentialsError, AuthenticationMethodNotAllowedError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email hoac password khong dung",
        )
    except (AuthenticationPolicyMissingError, AuthenticationPolicyInactiveError):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Authentication is not available",
        )
    except AccountLockedError as exc:
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail=f"Tai khoan tam khoa den {exc.locked_until.isoformat()}",
        )

    _set_session_cookie(response, result.session_token)

    return LocalLoginResponseSchema(
        status=result.status,
        mfa_challenge_id=result.mfa_challenge_id,
    )


@router.post(
    "/knowledge-spaces/{knowledge_space_id}/login/local",
    response_model=LocalLoginResponseSchema,
)
async def knowledge_space_login_local(
    knowledge_space_id: UUID,
    body: LocalLoginSchema,
    request: Request,
    response: Response,
    use_case: KnowledgeSpaceLocalLoginUseCase = Depends(
        get_knowledge_space_local_login_use_case,
    ),
) -> LocalLoginResponseSchema:
    try:
        result = await use_case.execute(
            KnowledgeSpaceLocalLoginRequest(
                knowledge_space_id=knowledge_space_id,
                email=body.email,
                password=body.password,
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent"),
                device_fingerprint=request.headers.get("x-device-fingerprint"),
            )
        )
    except (InvalidCredentialsError, AuthenticationMethodNotAllowedError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email hoac password khong dung",
        )
    except KnowledgeSpaceNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Knowledge Space not found",
        )
    except (AuthenticationPolicyMissingError, AuthenticationPolicyInactiveError):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Authentication is not available",
        )
    except AccountLockedError as exc:
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail=f"Tai khoan tam khoa den {exc.locked_until.isoformat()}",
        )

    _set_session_cookie(response, result.session_token)

    return LocalLoginResponseSchema(
        status=result.status,
        mfa_challenge_id=result.mfa_challenge_id,
    )


@router.post(
    "/management/login/entra/start",
    response_model=OidcStartResponseSchema,
)
async def management_login_entra_start(
    use_case: ManagementOidcStartUseCase = Depends(
        get_management_oidc_start_use_case,
    ),
) -> OidcStartResponseSchema:
    try:
        result = await use_case.execute()
    except AuthenticationMethodNotAllowedError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Microsoft Entra authentication is not allowed",
        )
    except (AuthenticationPolicyMissingError, AuthenticationPolicyInactiveError):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Authentication is not available",
        )
    return OidcStartResponseSchema(authorization_url=result.authorization_url)


@router.post(
    "/knowledge-spaces/{knowledge_space_id}/login/entra/start",
    response_model=OidcStartResponseSchema,
)
async def knowledge_space_login_entra_start(
    knowledge_space_id: UUID,
    use_case: KnowledgeSpaceOidcStartUseCase = Depends(
        get_knowledge_space_oidc_start_use_case,
    ),
) -> OidcStartResponseSchema:
    try:
        result = await use_case.execute(
            KnowledgeSpaceOidcStartRequest(
                knowledge_space_id=knowledge_space_id,
            )
        )
    except AuthenticationMethodNotAllowedError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Microsoft Entra authentication is not allowed",
        )
    except KnowledgeSpaceNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Knowledge Space not found",
        )
    except (AuthenticationPolicyMissingError, AuthenticationPolicyInactiveError):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Authentication is not available",
        )
    return OidcStartResponseSchema(authorization_url=result.authorization_url)


@router.get("/entra/callback")
async def complete_entra_login(
    request: Request,
    state: str,
    code: str | None = None,
    error: str | None = None,
    use_case: CompleteOidcUseCase = Depends(get_complete_oidc_use_case),
    frontend_redirect_url: str = Depends(get_auth_frontend_redirect_url),
) -> Response:
    if error is not None or code is None:
        try:
            await use_case.cancel(state)
        except (OidcStateInvalidError, OidcTransactionExpiredError):
            pass
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Microsoft Entra authentication was not completed",
        )
    try:
        result = await use_case.execute(
            CompleteOidcRequest(
                state=state,
                code=code,
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent"),
                device_fingerprint=request.headers.get("x-device-fingerprint"),
            )
        )
    except (OidcStateInvalidError, OidcTransactionExpiredError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OIDC transaction is invalid or expired",
        )
    except (OidcTokenValidationError, OidcTenantMismatchError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Microsoft Entra identity could not be verified",
        )
    except ExplicitAccountLinkRequiredError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This Microsoft Entra identity requires explicit account linking",
        )
    except AccountDisabledError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is not active",
        )

    redirect = RedirectResponse(
        url=append_auth_result(
            frontend_redirect_url,
            result.status,
            result.mfa_challenge_id,
        ),
        status_code=status.HTTP_303_SEE_OTHER,
    )
    _set_session_cookie(redirect, result.session_token)
    return redirect


def _set_session_cookie(response: Response, session_token: str | None) -> None:
    if session_token is None:
        return
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=session_token,
        httponly=True,
        secure=True,
        samesite="strict",
        path="/",
    )


@router.post(
    "/mfa/verify",
    response_model=LocalLoginResponseSchema,
)
async def verify_mfa(
    body: VerifyMfaSchema,
    response: Response,
    use_case: VerifyMfaUseCase = Depends(get_verify_mfa_use_case),
) -> LocalLoginResponseSchema:
    try:
        result = await use_case.execute(
            VerifyMfaRequest(
                challenge_id=body.challenge_id,
                code=body.code,
            )
        )
    except InvalidMfaChallengeError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="MFA challenge or code is invalid",
        )

    _set_session_cookie(response, result.session_token)
    return LocalLoginResponseSchema(status=result.status)


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
        user_id=current_user.user_id,
        email=current_user.email,
        context_type=current_user.context_type,
        auth_method=current_user.auth_method,
        knowledge_space_id=current_user.knowledge_space_id,
        authenticated_at=current_user.authenticated_at,
        mfa_verified=current_user.mfa_verified_at is not None,
    )


@router.post("/logout-all")
async def logout_all_sessions(
    response: Response,
    current_user=Depends(get_current_user),
    use_case: LogoutAllSessionsUseCase = Depends(
        get_logout_all_sessions_use_case,
    ),
) -> dict[str, bool]:
    await use_case.execute(
        LogoutAllSessionsRequest(
            user_id=current_user.user_id,
        )
    )
    response.delete_cookie(
        key=SESSION_COOKIE_NAME,
        path="/",
        samesite="strict",
    )
    return {"success": True}
