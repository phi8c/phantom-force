"""Bounded, optional structure hints; canonical content is never rewritten."""
import asyncio
from dataclasses import asdict
import json
import logging

from module.ingest.chunking.domain.contracts.structure_reviewer import ReviewWindow
from module.ingest.chunking.domain.contracts.review_hint_store import ReviewHintStore

logger = logging.getLogger(__name__)


def window_payload(window):
    return asdict(window)


def payload_size(window):
    return len(json.dumps(window_payload(window), ensure_ascii=False).encode('utf-8'))


class StructureReviewPlanner:
    def __init__(self, reviewer, *, max_window_bytes=32000, max_blocks=40,
                 timeout_seconds=600, review_structured=False):
        if max_window_bytes < 1024 or not 1 <= max_blocks <= 1000 or timeout_seconds <= 0:
            raise ValueError('Invalid structure review limits')
        self.reviewer = reviewer
        self.max_window_bytes = max_window_bytes
        self.max_blocks = max_blocks
        self.timeout_seconds = timeout_seconds
        self.review_structured = review_structured

    async def build(self, document_id, source, assignments: ReviewHintStore):
        pending, previous = [], None
        number = 0

        def window(blocks, context=None):
            values = ([context] if context else []) + blocks
            tables = tuple(source.table(b.table_id) for b in values if b.table_id)
            return ReviewWindow(str(document_id), str(number), tuple(values),
                                (context.id,) if context else (), tables)

        async def flush():
            nonlocal pending, previous, number
            if not pending:
                return
            current = window(pending)
            if previous is not None:
                contextual = window(pending, previous)
                if len(contextual.blocks) <= self.max_blocks and payload_size(contextual) <= self.max_window_bytes:
                    current = contextual
            try:
                result = await asyncio.wait_for(self.reviewer.review(current), self.timeout_seconds)
                result.validate_for(current)
            except Exception as exc:
                # Cancellation is BaseException and must propagate, never turn into success.
                logger.warning('structure_review fallback document_id=%s window_id=%s reason=%s',
                               document_id, number, type(exc).__name__)
            else:
                for index, group in enumerate(result.groups):
                    for block_id in group.block_ids:
                        assignments.put(block_id, f'review:{number}:{index}', group.title)
            previous = pending[-1]
            pending = []
            number += 1

        from .async_chunks import iterate_chunks
        from contextlib import aclosing
        async with aclosing(iterate_chunks(source.blocks())) as blocks:
            async for block in blocks:
                if block.section_id and not self.review_structured:
                    await flush()
                    previous = None
                    continue
                candidate = window([*pending, block])
                new_block_limit = max(1, self.max_blocks - (1 if previous is not None else 0))
                if pending and (len(candidate.blocks) > new_block_limit or payload_size(candidate) > self.max_window_bytes):
                    await flush()
                # Oversized blocks/tables go directly to the deterministic splitter.
                if payload_size(window([block])) > self.max_window_bytes:
                    previous = None
                    logger.info('structure_review oversized_block document_id=%s block_id=%s', document_id, block.id)
                    continue
                pending.append(block)
        await flush()
        assignments.finish()
