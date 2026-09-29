from uuid import UUID

from module.auth.application.dto.response.resolve_current_user_response import (
    ResolveCurrentUserResult,
)
from module.auth.domain.enums.authentication_context_type import (
    AuthenticationContextType,
)
from module.auth.domain.exception.exceptions import (
    InvalidAuthenticationContextError,
    KnowledgeSpaceContextMismatchError,
)


class AuthenticationContextGuard:
    def require_management(self, current_user: ResolveCurrentUserResult) -> None:
        if current_user.context_type is not AuthenticationContextType.MANAGEMENT:
            raise InvalidAuthenticationContextError(
                "Management authentication context is required"
            )

    def require_knowledge_space(
        self,
        current_user: ResolveCurrentUserResult,
        knowledge_space_id: UUID,
    ) -> None:
        if current_user.context_type is not AuthenticationContextType.KNOWLEDGE_SPACE:
            raise InvalidAuthenticationContextError(
                "Knowledge Space authentication context is required"
            )
        if current_user.knowledge_space_id != knowledge_space_id:
            raise KnowledgeSpaceContextMismatchError(
                "Session is not valid for this Knowledge Space"
            )
