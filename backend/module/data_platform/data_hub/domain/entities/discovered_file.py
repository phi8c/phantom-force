from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Mapping

from ..value_objects.source_reference import SourceReference


@dataclass(frozen=True, slots=True)
class DiscoveredFile:
    """
    Provider-neutral representation of a file discovered from a data source.
    """

    external_file_id: str
    file_name: str
    file_extension: str | None
    file_size_bytes: int | None
    source_file_url: str | None
    source: SourceReference
    provider_metadata: Mapping[str, object]
    last_modified_at: datetime | None
    original_file_path: str | None