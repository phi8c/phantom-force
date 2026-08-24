from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass
class KnowledgeSpaceDataHub:

    id: UUID | None

    knowledge_space_id: UUID

    data_hub_provider_id: UUID

    configuration: dict

    enabled: bool

    created_at: datetime | None

    updated_at: datetime | None