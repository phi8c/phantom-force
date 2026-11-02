from dataclasses import dataclass
from typing import Protocol

from shared.ingestion.document import ContentBlock, ExtractedTable


@dataclass(frozen=True)
class ReviewWindow:
    document_id: str
    window_id: str
    blocks: tuple[ContentBlock, ...]
    context_block_ids: tuple[str, ...] = ()
    tables: tuple[ExtractedTable, ...] = ()


@dataclass(frozen=True)
class ReviewedGroup:
    title: str | None
    block_ids: tuple[str, ...]


@dataclass(frozen=True)
class StructureReview:
    window_id: str
    groups: tuple[ReviewedGroup, ...]

    def validate_for(self, window: ReviewWindow) -> None:
        if self.window_id != window.window_id:
            raise ValueError("Review belongs to another window")
        source_ids = tuple(block.id for block in window.blocks)
        if len(set(source_ids)) != len(source_ids):
            raise ValueError("Duplicate source blocks")
        if not set(window.context_block_ids).issubset(source_ids):
            raise ValueError("Unknown context block")
        expected = tuple(value for value in source_ids if value not in window.context_block_ids)
        actual = tuple(value for group in self.groups for value in group.block_ids)
        if any(group.title is not None and (not isinstance(group.title, str) or len(group.title) > 160)
               for group in self.groups):
            raise ValueError("Review title must be text of at most 160 characters")
        if any(not group.block_ids for group in self.groups) or actual != expected:
            raise ValueError("Review must cover source blocks once, in order, without context")


class StructureReviewer(Protocol):
    """Suggest boundaries over source IDs, never rewrite source text.

    Application validates results and falls back to deterministic chunking.
    LLM/prompt adapters belong to infrastructure.
    """

    async def review(self, window: ReviewWindow) -> StructureReview:
        ...
