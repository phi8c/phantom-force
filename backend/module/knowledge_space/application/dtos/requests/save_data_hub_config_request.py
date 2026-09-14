from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class SaveDataHubConfigRequest:
    data_hub_provider_id: UUID
    configuration: dict
    enabled: bool = True
