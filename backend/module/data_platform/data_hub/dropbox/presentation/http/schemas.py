from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class DiscoverRequest(BaseModel):
    identifier: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    cursor: dict[str, Any] | None = None
    limit: int = Field(default=100, gt=0)


class BrowseNodeResponse(BaseModel):
    id: str
    name: str
    type: str
    path_lower: str | None
    path_display: str | None
    parent_path: str | None
    has_children: bool


class DiscoveredFileResponse(BaseModel):
    external_file_id: str
    file_name: str
    file_extension: str | None
    file_size_bytes: int | None
    source_file_url: str | None
    provider_metadata: dict[str, Any]
    last_modified_at: str | None
    original_file_path: str | None


class DiscoveryPageResponse(BaseModel):
    items: list[DiscoveredFileResponse]
    next_cursor: dict[str, Any] | None
    has_more: bool


class DownloadRequest(BaseModel):
    source_identifier: str
    external_file_id: str
    file_name: str
    file_extension: str | None = None
    file_size_bytes: int | None = None
    provider_metadata: dict[str, Any]
    original_file_path: str | None = None
