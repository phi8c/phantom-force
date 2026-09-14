from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class KnowledgeSpaceDataHubResponse:
    id: UUID
    knowledge_space_id: UUID
    data_hub_provider_id: UUID
    configuration: dict
    enabled: bool
    created_at: datetime | None
    updated_at: datetime | None


@dataclass(frozen=True)
class KnowledgeSpaceDataHubConfigResponse:
    configured: bool
    data: KnowledgeSpaceDataHubResponse | None
