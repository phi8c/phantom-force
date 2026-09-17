import logging
from collections.abc import Iterator
from uuid import UUID

from module.ingest.chunking.engine.contracts.chunk_strategy import (
    ChunkStrategy,
)

from module.ingest.chunking.engine.models.chunk import (
    Chunk,
)

from module.ingest.chunking.engine.models.document_extraction import (
    DocumentExtraction,
)


logger = logging.getLogger(__name__)


class LevelChunkStrategy(
    ChunkStrategy,
):

    def __init__(
        self,
        level: int,
    ):
        self.level = level

    def chunk(
        self,
        extraction: DocumentExtraction,
    ) -> Iterator[Chunk]:

        sections = (
            extraction
            .structured_content
            .get(
                "sections",
                [],
            )
        )

        root_sections = len(
            sections,
        )
        available_levels = _collect_section_levels(
            sections,
        )

        logger.info(
            "level_chunk start document_id=%s target_level=%s root_sections=%s",
            extraction.document_id,
            self.level,
            root_sections,
        )
        print(
            "level_chunk start "
            f"document_id={extraction.document_id} "
            f"target_level={self.level} "
            f"root_sections={root_sections}",
            flush=True,
        )

        sequence = 0
        matched_sections = 0

        for section in sections:

            for chunk in self._walk(
                section=section,
                document_id=(
                    extraction.document_id
                ),
                path_stack=[],
            ):
                matched_sections += 1

                chunk.sequence = (
                    sequence
                )

                sequence += 1

                yield chunk

        logger.info(
            "level_chunk done document_id=%s target_level=%s "
            "matched_sections=%s chunks=%s",
            extraction.document_id,
            self.level,
            matched_sections,
            sequence,
        )
        print(
            "level_chunk done "
            f"document_id={extraction.document_id} "
            f"target_level={self.level} "
            f"matched_sections={matched_sections} "
            f"chunks={sequence}",
            flush=True,
        )

        if sequence == 0:
            logger.warning(
                "level_chunk produced_zero_chunks document_id=%s "
                "target_level=%s root_sections=%s available_levels=%s",
                extraction.document_id,
                self.level,
                root_sections,
                available_levels,
            )
            print(
                "level_chunk produced_zero_chunks "
                f"document_id={extraction.document_id} "
                f"target_level={self.level} "
                f"root_sections={root_sections} "
                f"available_levels={available_levels}",
                flush=True,
            )

    def _walk(
        self,
        section: dict,
        document_id: UUID,
        path_stack: list[str],
    ) -> Iterator[Chunk]:

        path_stack.append(
            section["title"]
        )

        try:

            if (
                section["level"]
                == self.level
            ):

                yield self._create_chunk(
                    section=section,
                    document_id=document_id,
                    hierarchy_path=list(
                        path_stack
                    ),
                )

                return

            for child in (
                section.get(
                    "children",
                    [],
                )
            ):

                yield from self._walk(
                    section=child,
                    document_id=document_id,
                    path_stack=path_stack,
                )

        finally:

            path_stack.pop()

    def _create_chunk(
        self,
        section: dict,
        document_id: UUID,
        hierarchy_path: list[str],
    ) -> Chunk:

        return Chunk(
            document_id=document_id,

            source_section_id=(
                section["id"]
            ),

            sequence=0,

            title=section["title"],

            content=(
                self._collect_content(
                    section,
                )
            ),

            hierarchy_path=(
                hierarchy_path
            ),

            level=(
                section["level"]
            ),

            tables=[
                table["content"]
                for table in (
                    section.get(
                        "tables",
                        [],
                    )
                )
            ],

            image_captions=[
                image.get(
                    "caption",
                    "",
                )
                for image in (
                    section.get(
                        "images",
                        [],
                    )
                )
            ],

            metadata={
                "section_id": (
                    section["id"]
                ),
            },
        )

    def _collect_content(
        self,
        section: dict,
    ) -> str:

        parts: list[str] = []

        stack = [section]

        while stack:

            current = (
                stack.pop()
            )

            content = (
                current.get(
                    "content",
                )
                or ""
            )

            if content:

                parts.append(
                    content
                )

            children = (
                current.get(
                    "children",
                    [],
                )
            )

            for child in reversed(
                children
            ):

                stack.append(
                    child
                )

        return "\n\n".join(
            parts
        )


def _collect_section_levels(
    sections: list,
) -> list:

    levels = set()
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

        level = section.get(
            "level",
        )

        if level is not None:
            levels.add(
                level,
            )

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

    return sorted(
        levels,
        key=str,
    )
