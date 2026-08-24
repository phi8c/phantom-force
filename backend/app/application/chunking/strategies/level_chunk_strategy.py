from collections.abc import Iterator
from uuid import UUID

from app.application.chunking.contracts.chunk_strategy import (
    ChunkStrategy,
)

from app.domain.entities.chunk import (
    Chunk,
)

from app.domain.entities.document_extraction import (
    DocumentExtraction,
)


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

        sequence = 0

        for section in sections:

            for chunk in self._walk(
                section=section,
                document_id=(
                    extraction.document_id
                ),
                path_stack=[],
            ):

                chunk.sequence = (
                    sequence
                )

                sequence += 1

                yield chunk

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