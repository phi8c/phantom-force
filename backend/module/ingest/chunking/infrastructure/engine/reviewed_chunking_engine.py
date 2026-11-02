import asyncio
from contextlib import asynccontextmanager
import sqlite3
import tempfile

from .streaming_chunking_engine import StreamingChunkingEngine
from ..reading.review_hint_store import SqliteReviewHintStore


async def _thread_call(operation):
    """Wait for thread completion before callers close resources on cancellation."""
    task = asyncio.create_task(asyncio.to_thread(operation))
    try:
        return await asyncio.shield(task)
    except asyncio.CancelledError:
        await asyncio.gather(task, return_exceptions=True)
        raise


class ReviewedChunkingEngine(StreamingChunkingEngine):
    def __init__(self, *, review_planner, **kwargs):
        super().__init__(**kwargs)
        self.review_planner = review_planner

    @asynccontextmanager
    async def open_chunks(self, document):
        with tempfile.TemporaryDirectory(prefix='structure-review-') as directory:
            hints = sqlite3.connect(f'{directory}/hints.sqlite', check_same_thread=False)
            store = SqliteReviewHintStore(hints)
            context = self.reader.open(document.content_path)
            entered = False
            source = None

            def enter():
                nonlocal entered, source
                source = context.__enter__()
                entered = True

            try:
                await _thread_call(enter)
                await self.review_planner.build(document.document_id, source, store)

                def context_for(block):
                    row = store.get(block.id)
                    key, path = source.section_context(block.section_id,
                        self.planner.level if self.planner.strategy == 'SECTION' else None)
                    if row:
                        return row[0], (*path, row[1]) if row[1] else path
                    return key, path

                chunks = self.planner.chunks(source, context_for=context_for)
                try:
                    yield chunks
                finally:
                    await _thread_call(chunks.close)
            finally:
                try:
                    if entered:
                        await _thread_call(lambda: context.__exit__(None, None, None))
                finally:
                    hints.close()
