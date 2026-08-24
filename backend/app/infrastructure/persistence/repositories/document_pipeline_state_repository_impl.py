from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import (
    AsyncSession,
)

from app.domain.entities.document_pipeline_state import (
    DocumentPipelineState,
)

from app.domain.repositories.document_pipeline_state_repository import (
    DocumentPipelineStateRepository,
)

from app.infrastructure.persistence.mappers.document_pipeline_state_mapper import (
    DocumentPipelineStateMapper,
)

from app.infrastructure.persistence.models.document_pipeline_state_model import (
    DocumentPipelineStateModel,
)


class DocumentPipelineStateRepositoryImpl(
    DocumentPipelineStateRepository,
):

    def __init__(
        self,
        session: AsyncSession,
    ):
        self.session = session

    async def get_by_document_id(
        self,
        document_id: UUID,
    ) -> (
        DocumentPipelineState
        | None
    ):

        statement = select(
            DocumentPipelineStateModel
        ).where(
            DocumentPipelineStateModel.document_id
            == document_id
        )

        result = await (
            self.session.execute(
                statement,
            )
        )

        model = (
            result.scalar_one_or_none()
        )

        if not model:
            return None

        return (
            DocumentPipelineStateMapper.to_entity(
                model,
            )
        )

    async def create(
        self,
        state: DocumentPipelineState,
    ) -> DocumentPipelineState:

        model = (
            DocumentPipelineStateMapper.to_model(
                state,
            )
        )

        self.session.add(
            model,
        )

        await self.session.flush()

        return (
            DocumentPipelineStateMapper.to_entity(
                model,
            )
        )

    async def update(
        self,
        state: DocumentPipelineState,
    ) -> DocumentPipelineState:

        model = await (
            self.session.get(
                DocumentPipelineStateModel,
                state.document_id,
            )
        )

        if not model:

            raise ValueError(
                (
                    "DocumentPipelineState "
                    "not found"
                )
            )

        #
        # Data
        #
        model.chunks = (
            state.chunks
        )

        model.labels = (
            state.labels
        )

        model.embeddings = (
            state.embeddings
        )

        #
        # Flags
        #
        model.chunks_ready = (
            state.chunks_ready
        )

        model.classification_ready = (
            state.classification_ready
        )

        model.embedding_ready = (
            state.embedding_ready
        )

        model.index_event_published = (
            state.index_event_published
        )

        await self.session.flush()

        return (
            DocumentPipelineStateMapper.to_entity(
                model,
            )
        )