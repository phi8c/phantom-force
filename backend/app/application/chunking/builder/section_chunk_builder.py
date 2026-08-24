from app.domain.entities.chunk import (
    Chunk,
)


class SectionChunkBuilder:

    def build_from_level(
        self,
        sections: list[dict],
        target_level: int,
        document_id,
    ) -> list[Chunk]:

        chunks: list[Chunk] = []

        for section in sections:

            chunks.extend(
                self._collect_chunks(
                    section=section,
                    target_level=target_level,
                    document_id=document_id,
                    parent_path=[],
                )
            )

        return chunks

    def _collect_chunks(
        self,
        section: dict,
        target_level: int,
        document_id,
        parent_path: list[str],
    ) -> list[Chunk]:

        current_path = [
            *parent_path,
            section.get(
                "title",
                "",
            ),
        ]

        level = section.get(
            "level",
            0,
        )

        if level == target_level:

            return [
                Chunk(
                    document_id=document_id,

                    title=section.get(
                        "title",
                    ),

                    content=self._build_content(
                        section,
                    ),

                    hierarchy_path=current_path,

                    sequence=0,

                    metadata={
                        "section_id": section.get(
                            "id",
                        ),
                        "level": level,
                    },
                )
            ]

        chunks = []

        for child in section.get(
            "children",
            [],
        ):

            chunks.extend(
                self._collect_chunks(
                    section=child,
                    target_level=target_level,
                    document_id=document_id,
                    parent_path=current_path,
                )
            )

        return chunks

    def _build_content(
        self,
        section: dict,
    ) -> str:

        parts = []

        title = section.get(
            "title",
        )

        if title:
            parts.append(
                title,
            )

        content = section.get(
            "content",
        )

        if content:
            parts.append(
                content,
            )

        for table in section.get(
            "tables",
            [],
        ):

            table_content = table.get(
                "content",
            )

            if table_content:
                parts.append(
                    table_content,
                )

        return "\n\n".join(
            parts,
        )