from __future__ import annotations

from module.data_platform.common.microsoft_graph.client import (
    MicrosoftGraphClient,
)
from module.data_platform.data_hub.domain.contracts.file_downloader import (
    FileDownloader,
)
from module.data_platform.data_hub.domain.entities.discovered_file import (
    DiscoveredFile,
)


class SharePointFileDownloader(FileDownloader):
    """
    Downloads files discovered from SharePoint.
    """

    def __init__(
        self,
        graph_client: MicrosoftGraphClient,
    ) -> None:
        self._graph_client = graph_client

    async def download(
        self,
        file: DiscoveredFile,
    ) -> bytes:
        site_id = self._get_metadata(file, "site_id")
        drive_id = self._get_metadata(file, "drive_id")
        item_id = self._get_metadata(file, "item_id")

        endpoint = (
            f"/sites/{site_id}"
            f"/drives/{drive_id}"
            f"/items/{item_id}"
            f"/content"
        )

        return await self._graph_client.download(endpoint)

    @staticmethod
    def _get_metadata(
        file: DiscoveredFile,
        key: str,
    ) -> str:
        value = file.provider_metadata.get(key)

        if not value:
            raise ValueError(
                f"Missing SharePoint file metadata: {key}",
            )

        return str(value)