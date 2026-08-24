from app.domain.entities.document_pipeline_state import (
    DocumentPipelineState,
)

from app.infrastructure.persistence.models.document_pipeline_state_model import (
    DocumentPipelineStateModel,
)


class DocumentPipelineStateMapper:

    @staticmethod
    def to_entity(
        model: DocumentPipelineStateModel,
    ) -> DocumentPipelineState:

        return (
            DocumentPipelineState(
                document_id=model.document_id,

                chunks=model.chunks,

                labels=model.labels,

                embeddings=model.embeddings,

                chunks_ready=model.chunks_ready,

                classification_ready=(
                    model.classification_ready
                ),

                embedding_ready=(
                    model.embedding_ready
                ),

                index_event_published=(
                    model.index_event_published
                ),
            )
        )

    @staticmethod
    def to_model(
        entity: DocumentPipelineState,
    ) -> DocumentPipelineStateModel:

        return (
            DocumentPipelineStateModel(
                document_id=(
                    entity.document_id
                ),

                chunks=(
                    entity.chunks
                ),

                labels=(
                    entity.labels
                ),

                embeddings=(
                    entity.embeddings
                ),

                chunks_ready=(
                    entity.chunks_ready
                ),

                classification_ready=(
                    entity.classification_ready
                ),

                embedding_ready=(
                    entity.embedding_ready
                ),

                index_event_published=(
                    entity.index_event_published
                ),
            )
        )