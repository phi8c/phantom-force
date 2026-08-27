from collections.abc import AsyncIterator
from collections.abc import Callable
from typing import Awaitable
from uuid import UUID

from module.ingest.download.domain.contracts.document_source import (
    DocumentSource,
    DownloadSource,
)

from module.ingest.download.domain.contracts.download_document_reader import (
    DownloadDocumentReader,
    DownloadDocument,
)


StreamFactory = Callable[
    [DownloadDocument],
    AsyncIterator[bytes],
]


class DataHubDocumentSource(
    DocumentSource,
):

    def __init__(
        self,
        document_reader: DownloadDocumentReader,
        stream_factory: StreamFactory,
    ):
        self._document_reader = document_reader
        self._stream_factory = stream_factory

    async def open(
        self,
        document_id: UUID,
    ) -> DownloadSource:

        document = (
            await self._document_reader.get_by_id(
                document_id,
            )
        )

        if document is None:
            raise ValueError(
                "Document not found"
            )

        stream = self._stream_factory(
            document
        )

        return DownloadSource(
            content=stream,
            file_name=document.file_name,
            content_type=(
                self._resolve_content_type(
                    document
                )
            ),
            size_bytes=(
                document.file_size_bytes
            ),
        )

    @staticmethod
    def _resolve_content_type(
        document: DownloadDocument,
    ) -> str | None:

        mime_type = (
            document.provider_metadata.get(
                "mime_type"
            )
        )

        if mime_type:
            return str(mime_type)

        return None