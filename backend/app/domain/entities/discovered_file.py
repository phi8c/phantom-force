from dataclasses import dataclass
from datetime import datetime


@dataclass
class DiscoveredFile:

    external_file_id: str

    file_name: str

    file_extension: str | None

    file_size_bytes: int | None

    source_file_url: str | None

    provider_metadata: dict | None

    last_modified_at: datetime | None
    original_file_path: str | None