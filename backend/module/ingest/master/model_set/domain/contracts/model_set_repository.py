from abc import ABC
from abc import abstractmethod
from uuid import UUID

from module.ingest.master.model_set.domain.entities.model_set import (
    ModelSet,
)


class ModelSetRepository(ABC):

    @abstractmethod
    async def get_by_id(
        self,
        model_set_id: UUID,
    ) -> ModelSet | None:
        pass

    @abstractmethod
    async def get_by_code(
        self,
        code: str,
    ) -> ModelSet | None:
        pass
