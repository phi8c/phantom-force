from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class BrowseRequest(BaseModel):
    locator: dict[str, Any] = Field(default_factory=dict)


class DataHubBrowseNodeResponse(BaseModel):
    id: str
    name: str
    type: str
    has_children: bool
    provider: str
    locator: dict[str, Any]


class BrowseResponse(BaseModel):
    provider: str
    nodes: list[DataHubBrowseNodeResponse]
