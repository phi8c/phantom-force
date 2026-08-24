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
from app.application.chunking.utils.paragraph_splitter import (
    ParagraphSplitter,
)

class AutoChunkStrategy(
    ChunkStrategy,
):

    def __init__(
        self,
        level: int,
        max_chunk_tokens: int,
    ):
        self.level = level

        self.max_chunk_tokens = (
            max_chunk_tokens
        )
        
        
        self.paragraph_splitter = (
            ParagraphSplitter()
        )

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

        title = (
            section.get(
                "title",
            )
            or ""
        )

        path_stack.append(
            title,
        )

        try:

            level = (
                section.get(
                    "level",
                    0,
                )
            )

            aggregated_token_count = (
                section.get(
                    "aggregated_token_count",
                    0,
                )
            )

            children = (
                section.get(
                    "children",
                    [],
                )
            )

            if (
                level >= self.level
                and
                aggregated_token_count
                <= self.max_chunk_tokens
            ):

                yield self._create_chunk(
                    section=section,
                    document_id=document_id,
                    hierarchy_path=list(
                        path_stack,
                    ),
                )

                return

            if children:

                for child in children:

                    yield from self._walk(
                        section=child,
                        document_id=document_id,
                        path_stack=path_stack,
                    )

                return

            yield from self._split_leaf_section(
                section=section,
                document_id=document_id,
                hierarchy_path=list(
                    path_stack,
                ),
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
                section.get(
                    "id",
                    "",
                )
            ),

            sequence=0,

            title=section.get(
                "title",
            ),

            content=(
                section.get(
                    "aggregated_content",
                    "",
                )
            ),

            hierarchy_path=(
                hierarchy_path
            ),

            level=(
                section.get(
                    "level",
                    0,
                )
            ),

            tables=[
                table.get(
                    "content",
                    "",
                )
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
                if image.get(
                    "caption",
                )
            ],

            metadata={},
        )
        
    def _split_leaf_section(
        self,
        section: dict,
        document_id: UUID,
        hierarchy_path: list[str],
    ) -> Iterator[Chunk]:

        for paragraph in (
            self.paragraph_splitter.split(
                section.get(
                    "content",
                    "",
                )
            )
        ):

            yield Chunk(
                document_id=document_id,

                source_section_id=(
                    section.get(
                        "id",
                        "",
                    )
                ),

                sequence=0,

                title=section.get(
                    "title",
                ),

                content=paragraph,

                hierarchy_path=(
                    hierarchy_path
                ),

                level=(
                    section.get(
                        "level",
                        0,
                    )
                ),

                tables=[],

                image_captions=[],

                metadata={
                    "split_type": (
                        "paragraph"
                    )
                },
            )