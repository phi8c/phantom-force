from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from module.ingest.download.domain.contracts.download_document_reader import (
    DownloadDocument,
    DownloadDocumentReader,
)


class DownloadDocumentReaderImpl(
    DownloadDocumentReader,
):

    def __init__(
        self,
        session: AsyncSession,
    ):
        self.session = session

    async def get_by_id(
        self,
        document_id: UUID,
    ) -> DownloadDocument | None:

        statement = text(
            """
            SELECT
                id,
                file_name,
                file_size_bytes,
                file_extension,
                source_file_url,
                provider_metadata
            FROM documents
            WHERE id = :document_id
            """
        )

        result = await self.session.execute(
            statement,
            {
                "document_id": document_id,
            },
        )

        row = result.mappings().one_or_none()

        if row is None:
            return None

        return DownloadDocument(
            id=row["id"],
            file_name=row["file_name"],
            file_size_bytes=(
                row["file_size_bytes"]
            ),
            file_extension=(
                row["file_extension"]
            ),
            source_file_url=(
                row["source_file_url"]
            ),
            provider_metadata=(
                row["provider_metadata"]
                or {}
            ),
        )