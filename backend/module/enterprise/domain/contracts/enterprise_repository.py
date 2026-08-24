from abc import ABC
from abc import abstractmethod
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