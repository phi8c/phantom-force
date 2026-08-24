from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.document_extraction import (
    DocumentExtraction,
)
from app.domain.repositories.document_extraction_repository import (
    DocumentExtractionRepository,
)
from app.infrastructure.persistence.mappers.document_extraction_mapper import (
    DocumentExtractionMapper,
)
from app.infrastructure.persistence.models.document_extraction_model import (
    DocumentExtractionModel,
)

class DocumentExtractionRepositoryImpl(
    DocumentExtractionRepository,
):

    def __init__(
        self,
        session: AsyncSession,
    ):
        self.session = session

    async def create(
        self,
        extraction: DocumentExtraction,
    ) -> DocumentExtraction:

        model = (
            DocumentExtractionMapper.to_model(
                extraction,
            )
        )

        self.session.add(
            model,
        )

        await self.session.flush()

        return (
            DocumentExtractionMapper.to_domain(
                model,
            )
        )

    async def get_by_id(
        self,
        extraction_id: UUID,
    ) -> DocumentExtraction | None:

        result = await (
            self.session.execute(
                select(
                    DocumentExtractionModel,
                ).where(
                    DocumentExtractionModel.id
                    == extraction_id
                )
            )
        )

        model = (
            result.scalar_one_or_none()
        )

        if not model:
            return None

        return (
            DocumentExtractionMapper.to_domain(
                model,
            )
        )

    async def get_by_document_id(
        self,
        document_id: UUID,
    ) -> DocumentExtraction | None:

        result = await (
            self.session.execute(
                select(
                    DocumentExtractionModel,
                ).where(
                    DocumentExtractionModel.document_id
                    == document_id
                )
            )
        )

        model = (
            result.scalar_one_or_none()
        )

        if not model:
            return None

        return (
            DocumentExtractionMapper.to_domain(
                model,
            )
        )