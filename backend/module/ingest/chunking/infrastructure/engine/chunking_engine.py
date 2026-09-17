import json
import logging
from collections import Counter
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


logger = logging.getLogger(__name__)


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

        print(
            "\n===== CHUNKING INPUT RAW JSON START =====",
            flush=True,
        )
        print(
            f"document_id={document.document_id}",
            flush=True,
        )
        print(
            json.dumps(
                content,
                ensure_ascii=False,
                indent=2,
                default=str,
            ),
            flush=True,
        )
        print(
            "===== CHUNKING INPUT RAW JSON END =====\n",
            flush=True,
        )

        summary = _summarize_extracted_content(
            content,
        )
        logger.info(
            "chunking extracted_loaded document_id=%s "
            "content_type=%s top_level_keys=%s sections_count=%s",
            document.document_id,
            summary["content_type"],
            summary["top_level_keys"],
            summary["sections_count"],
        )
        print(
            "chunking extracted_loaded "
            f"document_id={document.document_id} "
            f"content_type={summary['content_type']} "
            f"top_level_keys={summary['top_level_keys']} "
            f"sections_count={summary['sections_count']}",
            flush=True,
        )

        if summary["section_levels"]:
            logger.info(
                "chunking extracted_loaded document_id=%s section_levels=%s",
                document.document_id,
                summary["section_levels"],
            )
            print(
                "chunking extracted_loaded "
                f"document_id={document.document_id} "
                f"section_levels={summary['section_levels']}",
                flush=True,
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
            print(
                "\n===== CHUNKING LEGACY CHUNK RAW START =====",
                flush=True,
            )
            print(
                f"document_id={document.document_id}",
                flush=True,
            )
            print(
                chunk,
                flush=True,
            )
            print(
                "===== CHUNKING LEGACY CHUNK RAW END =====\n",
                flush=True,
            )
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


def _summarize_extracted_content(
    content: object,
) -> dict:

    sections = []
    top_level_keys = []

    if isinstance(
        content,
        dict,
    ):
        top_level_keys = list(
            content.keys(),
        )
        raw_sections = content.get(
            "sections",
            [],
        )
        if isinstance(
            raw_sections,
            list,
        ):
            sections = raw_sections

    section_levels = Counter()
    sections_count = 0

    stack = list(
        reversed(
            sections,
        )
    )

    while stack:
        section = stack.pop()

        if not isinstance(
            section,
            dict,
        ):
            continue

        sections_count += 1
        level = section.get(
            "level",
        )

        if level is not None:
            section_levels[level] += 1

        children = section.get(
            "children",
            [],
        )

        if isinstance(
            children,
            list,
        ):
            stack.extend(
                reversed(
                    children,
                )
            )

    return {
        "content_type": type(content).__name__,
        "top_level_keys": top_level_keys,
        "sections_count": sections_count,
        "section_levels": dict(
            sorted(
                section_levels.items(),
                key=lambda item: str(
                    item[0],
                ),
            )
        ),
    }
