import asyncio
from dataclasses import asdict
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import AsyncMock
from uuid import uuid4

from shared.ingestion.document import (
    BlockKind, ContentBlock, DocumentSection, ExtractedDocumentV2, ExtractedTable,
    ExtractionMetadata, SourceLocation, StructureQuality, TableCell,
)
from module.ingest.chunking.domain.contracts.chunking_engine import ExtractedDocument
from module.ingest.chunking.domain.contracts.structure_reviewer import ReviewedGroup, StructureReview
from module.ingest.chunking.application.services.async_chunks import iterate_chunks
from module.ingest.chunking.application.services.structure_review import StructureReviewPlanner, payload_size
from module.ingest.chunking.infrastructure.engine.reviewed_chunking_engine import ReviewedChunkingEngine
from module.ingest.chunking.infrastructure.engine.llm_structure_reviewer import LLMStructureReviewer
from module.ingest.chunking.infrastructure.engine.streaming_chunking_engine import StreamingChunkingEngine


class Reviewer:
    def __init__(self, behavior=None):
        self.windows = []
        self.behavior = behavior

    async def review(self, window):
        self.windows.append(window)
        if self.behavior:
            return await self.behavior(window)
        ids = tuple(b.id for b in window.blocks if b.id not in window.context_block_ids)
        return StructureReview(window.window_id, (ReviewedGroup('Suggested title', ids),))


class StructureReviewTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / 'input.json'
        self.location = SourceLocation(native_block_index=0)

    def tearDown(self):
        self.temp.cleanup()

    def block(self, index, text='Original text', section=None):
        return ContentBlock(f'b{index}', index, BlockKind.PARAGRAPH, self.location,
                            text=text, section_id=section)

    def write(self, blocks, tables=(), sections=()):
        value = ExtractedDocumentV2('doc', 'Title', ExtractionMetadata('test', '1', StructureQuality.FLAT),
                                    tuple(blocks), tuple(tables), tuple(sections))
        self.path.write_text(json.dumps(asdict(value)), encoding='utf8')
        return ExtractedDocument(uuid4(), self.path)

    async def collect(self, document, reviewer, **config):
        engine = ReviewedChunkingEngine(review_planner=StructureReviewPlanner(reviewer, **config),
                                       max_chunk_tokens=1600)
        async with engine.open_chunks(document) as chunks:
            return [chunk async for chunk in iterate_chunks(chunks)]

    async def test_windows_overlap_only_as_context_and_preserve_content(self):
        document = self.write([self.block(i, f'Original {i}') for i in range(7)])
        reviewer = Reviewer()
        chunks = await self.collect(document, reviewer, max_blocks=3)
        self.assertEqual(len(reviewer.windows), 3)
        self.assertEqual(reviewer.windows[1].context_block_ids, ('b2',))
        self.assertEqual(reviewer.windows[2].context_block_ids, ('b4',))
        emitted = [v for chunk in chunks for v in chunk.metadata['source_block_ids']]
        self.assertEqual(emitted, [f'b{i}' for i in range(7)])
        self.assertTrue(all(chunk.title == 'Suggested title' for chunk in chunks))

    async def test_invalid_coverage_falls_back_without_source_loss(self):
        async def invalid(window):
            return StructureReview(window.window_id, (ReviewedGroup('Invented', ('b0', 'b0')),))
        document = self.write([self.block(0, 'A'), self.block(1, 'B')])
        chunks = await self.collect(document, Reviewer(invalid))
        self.assertEqual('\n\n'.join(c.content for c in chunks), 'A\n\nB')
        self.assertIsNone(chunks[0].title)

    async def test_timeout_falls_back(self):
        async def slow(window):
            await asyncio.sleep(1)
        document = self.write([self.block(0)])
        chunks = await self.collect(document, Reviewer(slow), timeout_seconds=.001)
        self.assertEqual(chunks[0].content, 'Original text')

    async def test_oversized_text_bypasses_review_and_is_fully_split(self):
        text = 'Long source. ' * 1000
        document = self.write([self.block(0, text)])
        reviewer = Reviewer()
        chunks = await self.collect(document, reviewer, max_window_bytes=1024)
        self.assertEqual(reviewer.windows, [])
        self.assertEqual(''.join(c.content for c in chunks), text)

    async def test_existing_structure_is_not_reviewed_by_default(self):
        document = self.write([self.block(0, section='s')], sections=[DocumentSection('s', 'Source title', 1)])
        reviewer = Reviewer()
        chunks = await self.collect(document, reviewer)
        self.assertEqual(reviewer.windows, [])
        self.assertEqual(chunks[0].title, 'Source title')

    async def test_explicit_review_of_structured_blocks(self):
        document = self.write([self.block(0, section='s')], sections=[DocumentSection('s', 'Source title', 1)])
        reviewer = Reviewer()
        chunks = await self.collect(document, reviewer, review_structured=True)
        self.assertEqual(len(reviewer.windows), 1)
        self.assertEqual(chunks[0].metadata['section_ids'], ['s'])

    async def test_tables_are_supplied_as_json_and_original_cells_survive(self):
        table = ExtractedTable('t', 2, 1, (TableCell(0, 0, 'Header'), TableCell(1, 0, 'Value')),
                               self.location, header_rows=(0,))
        block = ContentBlock('b0', 0, BlockKind.TABLE, self.location, table_id='t')
        document = self.write([block], [table])
        reviewer = Reviewer()
        chunks = await self.collect(document, reviewer)
        self.assertEqual(reviewer.windows[0].tables, (table,))
        self.assertIn('Value', chunks[0].content)
        self.assertEqual(chunks[0].metadata['source_block_ids'], ['b0'])

    async def test_byte_budget_is_respected_for_unicode(self):
        document = self.write([self.block(i, '\u0110i\u1ec7n \u00e1p ' * 10) for i in range(12)])
        reviewer = Reviewer()
        await self.collect(document, reviewer, max_window_bytes=1200)
        self.assertGreater(len(reviewer.windows), 1)
        self.assertTrue(all(payload_size(w) <= 1200 for w in reviewer.windows))

    async def test_cancel_propagates_and_reader_can_be_reopened(self):
        started = asyncio.Event()
        async def slow(window):
            started.set()
            await asyncio.Event().wait()
        document = self.write([self.block(0)])
        task = asyncio.create_task(self.collect(document, Reviewer(slow)))
        await started.wait()
        task.cancel()
        with self.assertRaises(asyncio.CancelledError):
            await task
        chunks = list(StreamingChunkingEngine().chunk(document))
        self.assertEqual(chunks[0].content, 'Original text')

    async def test_adapter_uses_prompt_and_rejects_rewritten_fields(self):
        prompts = SimpleNamespace(get_by_code=AsyncMock(return_value=SimpleNamespace(
            system_prompt='User supplied rules', configuration={})))
        gateway = SimpleNamespace(generate=AsyncMock(return_value=SimpleNamespace(content=json.dumps({
            'window_id': '0', 'groups': [{'title': None, 'block_ids': ['b0'], 'text': 'Rewritten'}]}))))
        adapter = LLMStructureReviewer(prompt_provider=prompts, llm_gateway=gateway,
                                      provider_code='provider', model_code='model')
        from module.ingest.chunking.domain.contracts.structure_reviewer import ReviewWindow
        with self.assertRaises(ValueError):
            await adapter.review(ReviewWindow('doc', '0', (self.block(0),)))
        self.assertEqual(gateway.generate.call_args.kwargs['system_prompt'], 'User supplied rules')

    async def test_missing_prompt_falls_back(self):
        prompts = SimpleNamespace(get_by_code=AsyncMock(return_value=None))
        gateway = SimpleNamespace(generate=AsyncMock())
        adapter = LLMStructureReviewer(prompt_provider=prompts, llm_gateway=gateway,
                                      provider_code='provider', model_code='model')
        chunks = await self.collect(self.write([self.block(0)]), adapter)
        self.assertEqual(chunks[0].content, 'Original text')
        gateway.generate.assert_not_called()

    async def test_context_emission_is_rejected_for_only_that_window(self):
        async def respond(window):
            ids = tuple(b.id for b in window.blocks)
            return StructureReview(window.window_id, (ReviewedGroup('Reviewed', ids),))
        reviewer = Reviewer(respond)
        document = self.write([self.block(i, f'Value {i}') for i in range(5)])
        chunks = await self.collect(document, reviewer, max_blocks=3)
        self.assertEqual(chunks[0].title, 'Reviewed')
        self.assertIsNone(chunks[-1].title)
        self.assertEqual([v for c in chunks for v in c.metadata['source_block_ids']],
                         [f'b{i}' for i in range(5)])

    async def test_adapter_accepts_valid_groups_and_keeps_input_intact(self):
        prompts = SimpleNamespace(get_by_code=AsyncMock(return_value=SimpleNamespace(
            system_prompt='Rules', configuration={'temperature': 0})))
        gateway = SimpleNamespace(generate=AsyncMock(return_value=SimpleNamespace(content=json.dumps({
            'window_id': '0', 'groups': [{'title': 'Reviewed', 'block_ids': ['b0']}]}))))
        adapter = LLMStructureReviewer(prompt_provider=prompts, llm_gateway=gateway,
                                      provider_code='provider', model_code='model')
        chunks = await self.collect(self.write([self.block(0, 'Exact original')]), adapter)
        self.assertEqual(chunks[0].content, 'Exact original')
        self.assertEqual(chunks[0].title, 'Reviewed')
        self.assertEqual(gateway.generate.call_args.kwargs['config'], {'temperature': 0})

    async def test_model_wait_does_not_block_event_loop(self):
        ticks = 0
        async def respond(window):
            await asyncio.sleep(.03)
            return StructureReview(window.window_id, (ReviewedGroup(None, ('b0',)),))
        async def heartbeat():
            nonlocal ticks
            for _ in range(5):
                await asyncio.sleep(.002)
                ticks += 1
        await asyncio.gather(self.collect(self.write([self.block(0)]), Reviewer(respond)), heartbeat())
        self.assertEqual(ticks, 5)
