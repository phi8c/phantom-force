from __future__ import annotations

import unittest
from uuid import UUID

from bootstrap.data_hub import create_download_stream_factory
from module.data_platform.data_hub.composition.downloader_registry import (
    DataHubDownloaderResource,
)
from module.ingest.download.domain.contracts.download_document_reader import (
    DownloadDocument,
)
from module.knowledge_space.application.services.data_hub_configuration_resolver import (
    ResolvedDataHubConfiguration,
)


class RecordingDownloader:
    def __init__(self, marker: str) -> None:
        self.marker = marker

    async def download(self, file) -> bytes:
        return self.marker.encode()

    async def download_stream(self, file):
        yield self.marker.encode()


class RecordingDownloaderRegistry:
    def __init__(self) -> None:
        self.calls = []

    def create(self, provider, configuration):
        self.calls.append((provider, dict(configuration)))
        return DataHubDownloaderResource(
            downloader=RecordingDownloader(configuration["marker"]),
        )


async def collect(stream) -> bytes:
    chunks = []
    async for chunk in stream:
        chunks.append(chunk)
    return b"".join(chunks)


class DownloadDataHubCompositionTests(unittest.IsolatedAsyncioTestCase):
    async def test_configuration_is_selected_per_runtime_context(self) -> None:
        registry = RecordingDownloaderRegistry()
        document = DownloadDocument(
            id=UUID("11111111-2222-3333-4444-555555555555"),
            file_name="file.txt",
            file_size_bytes=4,
            file_extension="txt",
            source_file_url=None,
            provider_metadata={"id": "dropbox-file"},
        )
        first = ResolvedDataHubConfiguration(
            data_hub_id=UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"),
            provider="dropbox",
            configuration={"marker": "ks-a"},
        )
        second = ResolvedDataHubConfiguration(
            data_hub_id=UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"),
            provider="dropbox",
            configuration={"marker": "ks-b"},
        )

        first_result = await collect(
            create_download_stream_factory(
                resolved=first,
                registry=registry,
            )(document)
        )
        second_result = await collect(
            create_download_stream_factory(
                resolved=second,
                registry=registry,
            )(document)
        )

        self.assertEqual(first_result, b"ks-a")
        self.assertEqual(second_result, b"ks-b")
        self.assertEqual(
            registry.calls,
            [
                ("dropbox", {"marker": "ks-a"}),
                ("dropbox", {"marker": "ks-b"}),
            ],
        )


if __name__ == "__main__":
    unittest.main()
