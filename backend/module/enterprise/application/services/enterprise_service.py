import base64
import json
from datetime import datetime
from uuid import UUID

from sqlalchemy.exc import IntegrityError

from module.enterprise.application.dtos import (
    CreateEnterpriseRequest,
    EnterpriseResponse,
    ListEnterprisesRequest,
    ListEnterprisesResponse,
    UpdateEnterpriseRequest,
)
from module.enterprise.domain.contracts.enterprise_repository import (
    EnterpriseRepository,
)
from module.enterprise.domain.entities.enterprise import Enterprise


class EnterpriseService:

    def __init__(
        self,
        *,
        repository: EnterpriseRepository,
        session,
    ):
        self.repository = repository
        self.session = session

    async def create(
        self,
        request: CreateEnterpriseRequest,
    ) -> EnterpriseResponse:

        self._validate_code(
            request.code,
        )
        self._validate_name(
            request.name,
        )

        existing = await self.repository.get_by_code(
            request.code,
        )

        if existing is not None:
            raise ValueError(
                "Enterprise code already exists"
            )

        try:
            enterprise = await self.repository.create(
                Enterprise(
                    id=None,
                    code=request.code,
                    name=request.name,
                    description=request.description,
                    status=request.status.value,
                    created_at=None,
                    updated_at=None,
                )
            )

            await self.session.commit()

        except IntegrityError as exc:
            await self.session.rollback()
            raise ValueError(
                "Enterprise code already exists"
            ) from exc

        return self._to_response(
            enterprise,
        )

    async def get(
        self,
        enterprise_id: UUID,
    ) -> EnterpriseResponse | None:

        enterprise = await self.repository.get_by_id(
            enterprise_id,
        )

        if enterprise is None:
            return None

        return self._to_response(
            enterprise,
        )

    async def update(
        self,
        enterprise_id: UUID,
        request: UpdateEnterpriseRequest,
    ) -> EnterpriseResponse | None:

        enterprise = await self.repository.get_by_id(
            enterprise_id,
        )

        if enterprise is None:
            return None

        if request.code is not None:
            self._validate_code(
                request.code,
            )
            existing = await self.repository.get_by_code(
                request.code,
            )

            if (
                existing is not None
                and existing.id != enterprise_id
            ):
                raise ValueError(
                    "Enterprise code already exists"
                )

            enterprise.code = request.code

        if request.name is not None:
            self._validate_name(
                request.name,
            )
            enterprise.name = request.name

        if request.description_provided:
            enterprise.description = request.description

        if request.status is not None:
            enterprise.status = request.status.value

        try:
            enterprise = await self.repository.update(
                enterprise,
            )

            await self.session.commit()

        except IntegrityError as exc:
            await self.session.rollback()
            raise ValueError(
                "Enterprise code already exists"
            ) from exc

        return self._to_response(
            enterprise,
        )

    async def list_page(
        self,
        request: ListEnterprisesRequest,
    ) -> ListEnterprisesResponse:

        if request.limit <= 0 or request.limit > 100:
            raise ValueError(
                "limit must be between 1 and 100"
            )

        cursor_created_at = None
        cursor_id = None

        if request.cursor:
            cursor_created_at, cursor_id = self._decode_cursor(
                request.cursor,
            )

        enterprises = await self.repository.list_page(
            limit=request.limit + 1,
            cursor_created_at=cursor_created_at,
            cursor_id=cursor_id,
        )

        has_more = len(enterprises) > request.limit
        items = enterprises[: request.limit]
        next_cursor = None

        if has_more and items:
            next_cursor = self._encode_cursor(
                items[-1],
            )

        return ListEnterprisesResponse(
            items=[
                self._to_response(enterprise)
                for enterprise in items
            ],
            next_cursor=next_cursor,
            has_more=has_more,
        )

    async def list_enabled(
        self,
    ) -> list[EnterpriseResponse]:

        enterprises = await self.repository.list_enabled()

        return [
            self._to_response(enterprise)
            for enterprise in enterprises
        ]

    @staticmethod
    def _validate_code(
        code: str,
    ) -> None:
        if not code or not code.strip():
            raise ValueError(
                "Enterprise code is required"
            )

    @staticmethod
    def _validate_name(
        name: str,
    ) -> None:
        if not name or not name.strip():
            raise ValueError(
                "Enterprise name is required"
            )

    @staticmethod
    def _to_response(
        enterprise: Enterprise,
    ) -> EnterpriseResponse:
        if enterprise.id is None:
            raise ValueError(
                "Enterprise id is required"
            )

        return EnterpriseResponse(
            id=enterprise.id,
            code=enterprise.code,
            name=enterprise.name,
            description=enterprise.description,
            status=enterprise.status,
            created_at=enterprise.created_at,
            updated_at=enterprise.updated_at,
        )

    @staticmethod
    def _encode_cursor(
        enterprise: Enterprise,
    ) -> str:
        if enterprise.id is None or enterprise.created_at is None:
            raise ValueError(
                "Enterprise cursor fields are required"
            )

        payload = json.dumps(
            {
                "created_at": enterprise.created_at.isoformat(),
                "id": str(enterprise.id),
            },
            separators=(
                ",",
                ":",
            ),
        ).encode("utf-8")

        return (
            base64.urlsafe_b64encode(payload)
            .decode("ascii")
            .rstrip("=")
        )

    @staticmethod
    def _decode_cursor(
        cursor: str,
    ) -> tuple[datetime, UUID]:
        try:
            padded_cursor = cursor + (
                "=" * (-len(cursor) % 4)
            )
            payload = json.loads(
                base64.urlsafe_b64decode(
                    padded_cursor.encode("ascii")
                ).decode("utf-8")
            )
            return (
                datetime.fromisoformat(
                    payload["created_at"],
                ),
                UUID(
                    payload["id"],
                ),
            )
        except Exception as exc:
            raise ValueError(
                "Invalid enterprise pagination cursor"
            ) from exc
