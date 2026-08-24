from dataclasses import dataclass
from uuid import UUID


@dataclass(slots=True)
class SaveExtractionStorageMessage:

    extraction_id: UUID