from abc import ABC
from abc import abstractmethod
from dataclasses import dataclass
from dataclasses import field
from datetime import datetime
from typing import Any
from typing import Mapping


@dataclass(frozen=True, slots=True)
class SourceReference:
    provider: str
    identifier: str
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class DiscoveredFile:
    external_file_id: str
    file_name: str
    file_extension: str | None
    file_size_bytes: int | None
    source_file_url: str | None
    provider_metadata: Mapping[str, object]
    last_modified_at: datetime | None
    original_file_path: str | None


@dataclass
class DiscoveryPage:
    items: list[DiscoveredFile]
    next_cursor: dict[str, Any] | None
    has_more: bool


class DiscoveryProvider(ABC):

    @abstractmethod
    async def discover(
        self,
        source: SourceReference,
        *,
        cursor: dict[str, Any] | None = None,
        limit: int = 100,
    ) -> DiscoveryPage:
        pass
