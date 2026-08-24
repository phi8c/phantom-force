from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass
class IngestionSource:

    id: UUID

    name: str

    source_type: str

    provider_type: str

    provider_configuration: dict

    enabled: bool