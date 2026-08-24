from uuid import UUID

from app.domain.entities.chunk import (
    Chunk,
)


class ChunkSerializer:

    @staticmethod
    def to_dict(
        chunk: Chunk,
    ) -> dict:

        return {
            "document_id": str(
                chunk.document_id,
            ),
            "source_section_id": (
                chunk.source_section_id
            ),
            "sequence": (
                chunk.sequence
            ),
            "title": (
                chunk.title
            ),
            "content": (
                chunk.content
            ),
            "hierarchy_path": (
                chunk.hierarchy_path
            ),
            "level": (
                chunk.level
            ),
            "tables": (
                chunk.tables
            ),
            "image_captions": (
                chunk.image_captions
            ),
            "metadata": (
                chunk.metadata
            ),
        }

    @staticmethod
    def from_dict(
        payload: dict,
    ) -> Chunk:

        return Chunk(
            document_id=UUID(
                payload[
                    "document_id"
                ]
            ),
            source_section_id=(
                payload[
                    "source_section_id"
                ]
            ),
            sequence=(
                payload[
                    "sequence"
                ]
            ),
            title=(
                payload[
                    "title"
                ]
            ),
            content=(
                payload[
                    "content"
                ]
            ),
            hierarchy_path=(
                payload[
                    "hierarchy_path"
                ]
            ),
            level=(
                payload[
                    "level"
                ]
            ),
            tables=(
                payload[
                    "tables"
                ]
            ),
            image_captions=(
                payload[
                    "image_captions"
                ]
            ),
            metadata=(
                payload[
                    "metadata"
                ]
            ),
        )