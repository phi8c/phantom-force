from __future__ import annotations

from dataclasses import dataclass

from .infrastructure.browser import DropboxBrowseProvider
from .infrastructure.discovery import DropboxDiscoveryProvider
from .infrastructure.downloader import DropboxFileDownloader


@dataclass(frozen=True, slots=True)
class DropboxProvider:
    browser: DropboxBrowseProvider
    discovery: DropboxDiscoveryProvider
    downloader: DropboxFileDownloader
