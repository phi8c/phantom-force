from module.ingest.chunking.domain.contracts.chunk_batch_writer import (
    ChunkBatch,
)
from module.ingest.chunking.infrastructure.persistence.models.chunk_batch_model import (
    ChunkBatchModel,
)


class ChunkBatchMapper:

    @staticmethod
    def to_entity(
        model: ChunkBatchModel,
    ) -> ChunkBatch:

        if model.ingestion_job_id is None:
            raise ValueError(
                "ChunkBatch ingestion_job_id is required"
            )

        return ChunkBatch(
            id=model.id,
            ingestion_job_id=model.ingestion_job_id,
            document_id=model.document_id,
            total_chunks=model.total_chunks,
        )
