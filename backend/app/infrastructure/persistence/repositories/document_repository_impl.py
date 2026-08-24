from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.document import (
    Document,
)

from app.domain.repositories.document_repository import (
    DocumentRepository,
)

from app.infrastructure.persistence.mappers.document_mapper import (
    DocumentMapper,
)

from app.infrastructure.persistence.models.document_model import (
    DocumentModel,
)

from app.shared.repositories.base_repository import (
    BaseRepository,
)


class DocumentRepositoryImpl(
    BaseRepository[DocumentModel],
    DocumentRepository,
):

    def __init__(
        self,
        session: AsyncSession,
    ):
        super().__init__(
            session=session,
            model=DocumentModel,
        )

    async def get_by_id(
        self,
        document_id: UUID,
    ) -> Document | None:

        model = await super().get_by_id(
            document_id,
        )

        if not model:
            return None

        return (
            DocumentMapper.to_entity(
                model,
            )
        )

    async def get_by_external_file_id(
        self,
        source_id: UUID,
        external_file_id: str,
    ) -> Document | None:

        result = await (
            self.session.execute(
                select(
                    DocumentModel,
                ).where(
                    DocumentModel.source_id
                    == source_id,
                    DocumentModel.external_file_id
                    == external_file_id,
                )
            )
        )

        model = (
            result.scalar_one_or_none()
        )

        if not model:
            return None

        return (
            DocumentMapper.to_entity(
                model,
            )
        )

    async def get_by_external_file_ids(
        self,
        source_id: UUID,
        external_file_ids: list[str],
    ) -> dict[str, Document]:

        if not external_file_ids:
            return {}

        result = await (
            self.session.execute(
                select(
                    DocumentModel,
                ).where(
                    DocumentModel.source_id
                    == source_id,
                    DocumentModel.external_file_id.in_(
                        external_file_ids,
                    ),
                )
            )
        )

        models = (
            result.scalars().all()
        )

        return {
            model.external_file_id:
            DocumentMapper.to_entity(
                model,
            )
            for model in models
        }

    async def create(
        self,
        document: Document,
    ) -> Document:

        model = (
            DocumentMapper.to_model(
                document,
            )
        )

        created_model = await (
            self.add(
                model,
            )
        )

        return (
            DocumentMapper.to_entity(
                created_model,
            )
        )

    async def update(
        self,
        document: Document,
    ) -> None:

        model = await (
            super().get_by_id(
                document.id,
            )
        )

        if not model:
            raise ValueError(
                "Document not found",
            )

        model.external_file_id = (
            document.external_file_id
        )

        model.provider_metadata = (
            document.provider_metadata
        )

        model.file_name = (
            document.file_name
        )

        model.department = (
            document.department
        )

        model.owner_role = (
            document.owner_role
        )

        model.security_level = (
            document.security_level
        )

        model.document_type = (
            document.document_type
        )

        model.source_file_url = (
            document.source_file_url
        )

        model.file_extension = (
            document.file_extension
        )

        model.file_size_bytes = (
            document.file_size_bytes
        )

        model.content_hash = (
            document.content_hash
        )

        model.processing_status = (
            document.processing_status
        )

        model.processing_error = (
            document.processing_error
        )

        model.temp_file_path = (
            document.temp_file_path
        )
        model.original_file_path = (
            document.original_file_path
        )

        model.last_modified_at = (
            document.last_modified_at
        )

        model.last_ingested_at = (
            document.last_ingested_at
        )

        await self.session.flush()