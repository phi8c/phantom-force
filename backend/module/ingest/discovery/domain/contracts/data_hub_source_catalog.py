from abc import ABC
from abc import abstractmethod
from dataclasses import dataclass
from typing import Any
from uuid import UUID


@dataclass(frozen=True)
class IngestionSourceConfig:
    data_hub_id: UUID
    provider: str
    configuration: dict[str, Any]
    scope_data: dict[str, Any]


class DataHubSourceCatalog(ABC):

    @abstractmethod
    async def get_for_ingestion_job(
        self,
        ingestion_job_id: UUID,
    ) -> IngestionSourceConfig | None:
        pass
