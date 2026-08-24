from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class SourceReferenceRequest(BaseModel):
    provider: str
    identifier: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class DiscoveredFileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    external_file_id: str
    file_name: str
    file_extension: str | None
    file_size_bytes: int | None
    source_file_url: str | None
    provider_metadata: dict[str, Any]
    last_modified_at: str | None
    original_file_path: str | None