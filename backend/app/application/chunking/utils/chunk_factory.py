from app.domain.entities.chunk import (
    Chunk,
)


class ChunkFactory:

    @staticmethod
    def create_section_chunk(
        *,
        document_id,
        section,
        hierarchy_path,
        content,
    ) -> Chunk:

        return Chunk(
            document_id=document_id,

            source_section_id=(
                section.id
            ),

            sequence=0,

            title=section.title,

            content=content,

            hierarchy_path=(
                hierarchy_path
            ),

            level=section.level,

            tables=[
                table.content
                for table in (
                    section.tables
                )
            ],

            image_captions=[
                image.caption
                for image in (
                    section.images
                )
                if image.caption
            ],

            metadata={},
        )