from __future__ import annotations

from typing import Protocol

from ..entities.client_models import DropboxListPage


class DropboxClient(Protocol):
    async def list_folder(self, path: str, *, recursive: bool) -> DropboxListPage: ...
    async def list_folder_continue(self, cursor: str) -> DropboxListPage: ...
    async def download(self, identity: str) -> bytes: ...
