import json
from collections.abc import Iterable

from module.ingest.chunking.domain.contracts.chunking_engine import (
    Chunk,
    ChunkingEngine,
    ExtractedDocument,
)
from module.ingest.chunking.engine.chunking_engine import (
    ChunkingEngine as LegacyChunkingEngine,
)
from module.ingest.chunking.engine.contracts.chunk_strategy import (
    ChunkStrategy,
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
        strategy: ChunkStrategy | None = None,
    ):
        self._engine = (
            engine
            or LegacyChunkingEngine(
                strategy=(
                    strategy
                    or AutoChunkStrategy(
                        level=2,
                        max_chunk_tokens=800,
                    )
                ),
            )
        )

    def chunk(
        self,
        document: ExtractedDocument,
    ) -> Iterable[Chunk]:

        with document.content_path.open(
            "r",
            encoding="utf-8",
        ) as file:
            content = json.load(
                file,
            )

        extraction = DocumentExtraction(
            id=None,
            document_id=document.document_id,
            structured_content=content,
            page_count=(
                content.get(
                    "page_count"
                )
                if isinstance(
                    content,
                    dict,
                )
                else None
            ),
            created_at=None,
        )

        for chunk in self._engine.chunk(
            extraction,
        ):
            yield Chunk(
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
