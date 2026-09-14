from abc import ABC
from abc import abstractmethod
from datetime import datetime
from uuid import UUID

from module.enterprise.domain.entities.enterprise import (
    Enterprise,
)


class EnterpriseRepository(
    ABC,
):

    @abstractmethod
    async def get_by_id(
        self,
        enterprise_id: UUID,
    ) -> Enterprise | None:
        pass

    @abstractmethod
    async def get_by_code(
        self,
        code: str,
    ) -> Enterprise | None:
        pass

    @abstractmethod
    async def create(
        self,
        enterprise: Enterprise,
    ) -> Enterprise:
        pass

    @abstractmethod
    async def update(
        self,
        enterprise: Enterprise,
    ) -> Enterprise:
        pass

    @abstractmethod
    async def list_page(
        self,
        *,
        limit: int,
        cursor_created_at: datetime | None = None,
        cursor_id: UUID | None = None,
    ) -> list[Enterprise]:
        pass

    @abstractmethod
    async def list_enabled(
        self,
    ) -> list[Enterprise]:
        pass
