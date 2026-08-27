from module.ingest.chunking.domain.contracts.chunking_engine import (
    Chunk,
    ChunkingEngine,
    ExtractedDocument,
)
from module.ingest.chunking.engine.chunking_engine import (
    ChunkingEngine as LegacyChunkingEngine,
)
from module.ingest.chunking.engine.models.document_extraction import (
    DocumentExtraction,
)
from module.ingest.chunking.engine.strategies.auto_chunk_strategy import (
    AutoChunkStrategy,
)


class LegacyChunkingEngineAdapter(
    ChunkingEngine,
):

    def __init__(
        self,
        engine: LegacyChunkingEngine | None = None,
    ):
        self._engine = (
            engine
            or LegacyChunkingEngine(
                strategy=AutoChunkStrategy(
                    level=2,
                    max_chunk_tokens=800,
                )
            )
        )

    async def chunk(
        self,
        document: ExtractedDocument,
    ) -> list[Chunk]:

        extraction = DocumentExtraction(
            id=None,
            document_id=document.document_id,
            structured_content=document.content,
            page_count=(
                document.content.get(
                    "page_count"
                )
                if isinstance(
                    document.content,
                    dict,
                )
                else None
            ),
            created_at=None,
        )

        chunks = list(
            self._engine.chunk(
                extraction,
            )
        )

        return [
            Chunk(
                index=chunk.sequence,
                title=chunk.title,
                content=chunk.content,
                metadata={
                    **(
                        chunk.metadata
                        or {}
                    ),
                    "source_section_id": (
                        chunk.source_section_id
                    ),
                    "hierarchy_path": (
                        chunk.hierarchy_path
                    ),
                    "level": chunk.level,
                    "tables": chunk.tables,
                    "image_captions": (
                        chunk.image_captions
                    ),
                },
            )
            for chunk in chunks
        ]
