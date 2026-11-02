import asyncio
from dataclasses import replace
import json
from pathlib import Path
import tempfile
import unittest
import importlib.util
from zipfile import ZipFile

from shared.ingestion.parts import ExtractionManifest, ExtractionPart, PartStatus
from shared.ingestion.document import SourceLocation
from module.ingest.extraction.infrastructure.normalization.native_docx import NativeDocxReader
from module.ingest.extraction.infrastructure.normalization.document_builder import serialize_document, NormalizedDocumentBuilder
from module.ingest.extraction.infrastructure.normalization.document_codec import decode_document
from module.ingest.extraction.infrastructure.multipart.engine import MultipartExtractionEngine
from module.ingest.extraction.infrastructure.multipart.checkpoints import atomic_json, checksum, CacheLock
from module.ingest.extraction.infrastructure.multipart.partitioner import SourcePartitioner
from module.ingest.extraction.infrastructure.multipart.assembler import assemble
from module.ingest.extraction.infrastructure.multipart.process_executor import ProcessPartExecutor
from module.ingest.extraction.domain.contracts.extraction_parts import PartExecutionError


class LocalExecutor:
    def __init__(self, *, fail_names=(), max_blocks=None):
        self.calls = []
        self.fail_names = set(fail_names)
        self.max_blocks = max_blocks

    async def execute(self, source, destination):
        self.calls.append(source.stem)
        document = NativeDocxReader().read(source)
        if source.stem in self.fail_names or (self.max_blocks and len(document.blocks) > self.max_blocks):
            raise RuntimeError('Synthetic part failure')
        atomic_json(destination, serialize_document(document))


class MultipartExtractionTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.source = self.root / 'source.docx'
        with ZipFile(self.source, 'w') as archive:
            archive.writestr('word/document.xml',
                '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body>'
                + ''.join(f'<w:p><w:r><w:t>Paragraph {i}</w:t></w:r></w:p>' for i in range(5))
                + '</w:body></w:document>')

    def tearDown(self):
        self.temporary.cleanup()

    def engine(self, executor, **settings):
        return MultipartExtractionEngine('docling',
            {'extraction_runtime': {'docx_blocks_per_part': 2, 'part_max_attempts': 1, **settings}},
            executor=executor, cache_root=self.root / 'cache')

    async def test_partition_resume_and_global_source_mapping(self):
        executor = LocalExecutor()
        engine = self.engine(executor)
        result = await engine.extract(self.source)
        payload = json.loads(result.content_file.read_text(encoding='utf-8'))
        decode_document(payload)
        self.assertEqual(payload['title'], self.source.stem)
        self.assertEqual([block['text'] for block in payload['blocks']], [f'Paragraph {i}' for i in range(5)])
        self.assertEqual([block['source']['native_block_index'] for block in payload['blocks']], list(range(5)))
        self.assertEqual(len({block['id'] for block in payload['blocks']}), 5)
        self.assertEqual(len(executor.calls), 3)
        await engine.extract(self.source)
        self.assertEqual(len(executor.calls), 3)

    async def test_failed_ranges_are_bisected_without_losing_content(self):
        executor = LocalExecutor(max_blocks=1)
        result = await self.engine(executor).extract(self.source)
        payload = json.loads(result.content_file.read_text(encoding='utf-8'))
        self.assertEqual(len(payload['blocks']), 5)
        manifest = json.loads((result.content_file.parent / 'manifest.json').read_text())
        self.assertEqual(len(manifest['parts']), 5)
        self.assertTrue(all(part['status'] == 'completed' for part in manifest['parts']))

    async def test_failed_run_reuses_completed_parts(self):
        first = LocalExecutor(fail_names={'native_block-4-4'})
        with self.assertRaisesRegex(RuntimeError, 'smallest source range'):
            await self.engine(first).extract(self.source)
        second = LocalExecutor()
        await self.engine(second).extract(self.source)
        self.assertEqual(second.calls, ['native_block-4-4'])

    async def test_corrupt_checkpoint_artifact_is_recomputed(self):
        executor = LocalExecutor()
        engine = self.engine(executor)
        result = await engine.extract(self.source)
        (result.content_file.parent / 'native_block-0-1.json').write_text('corrupt')
        executor.calls.clear()
        await engine.extract(self.source)
        self.assertEqual(executor.calls, ['native_block-0-1'])

    async def test_source_change_uses_a_different_cache(self):
        first = await self.engine(LocalExecutor()).extract(self.source)
        with ZipFile(self.source, 'a') as archive:
            archive.writestr('extra.txt', 'changed')
        second = await self.engine(LocalExecutor()).extract(self.source)
        self.assertNotEqual(first.content_file.parent, second.content_file.parent)

    async def test_config_change_invalidates_cache(self):
        first = await self.engine(LocalExecutor()).extract(self.source)
        second = await self.engine(LocalExecutor(), docx_blocks_per_part=3).extract(self.source)
        self.assertNotEqual(first.content_file.parent, second.content_file.parent)

    async def test_cancelled_part_is_recoverable_and_lock_released(self):
        started = asyncio.Event()

        class WaitingExecutor:
            async def execute(self, source, destination):
                started.set()
                await asyncio.Event().wait()

        operation = asyncio.create_task(self.engine(WaitingExecutor()).extract(self.source))
        await started.wait()
        operation.cancel()
        with self.assertRaises(asyncio.CancelledError):
            await operation
        result = await self.engine(LocalExecutor()).extract(self.source)
        self.assertTrue(result.content_file.is_file())

    async def test_pdf_page_offsets_and_cross_part_heading_context(self):
        directory = self.root / 'manual'
        directory.mkdir()
        parts = []
        for index in range(2):
            builder = NormalizedDocumentBuilder('doc', 'Title', 'fake', '1')
            builder.add_text('Heading' if index == 0 else 'Continuation', SourceLocation(page_number=1),
                             level=1 if index == 0 else None)
            artifact = directory / f'p{index}.json'
            atomic_json(artifact, serialize_document(builder.build()))
            parts.append(ExtractionPart(f'p{index}', index, PartStatus.COMPLETED,
                                       index + 1, index + 1, artifact.name, checksum(artifact)))
        manifest = ExtractionManifest('doc', 'hash', 'config', 'page', tuple(parts))
        _, output = assemble(directory, manifest, 'fake')
        payload = json.loads(output.read_text())
        self.assertEqual([block['source']['page_number'] for block in payload['blocks']], [1, 2])
        self.assertEqual(payload['blocks'][0]['section_id'], payload['blocks'][1]['section_id'])
        decode_document(payload)

    async def test_cache_lock_rejects_concurrent_writer(self):
        first = CacheLock(self.root / 'lock')
        second = CacheLock(self.root / 'lock')
        first.acquire()
        try:
            with self.assertRaises(RuntimeError):
                second.acquire()
        finally:
            first.release()

    async def test_actual_subprocess_extracts_native_docx_without_model(self):
        output = self.root / 'subprocess.json'
        await ProcessPartExecutor('docling', timeout_seconds=30).execute(self.source, output)
        payload = json.loads(output.read_text(encoding='utf-8'))
        decode_document(payload)
        self.assertEqual(len(payload['blocks']), 5)

    async def test_permanent_provider_error_does_not_bisect_every_range(self):
        class UnauthorizedExecutor:
            def __init__(self):
                self.calls = 0

            async def execute(self, source, destination):
                self.calls += 1
                raise PartExecutionError('Unauthorized', can_split=False, retryable=False)

        executor = UnauthorizedExecutor()
        with self.assertRaises(RuntimeError):
            await self.engine(executor, part_max_attempts=3).extract(self.source)
        self.assertEqual(executor.calls, 1)

    async def test_blank_part_is_retained_but_empty_document_is_rejected(self):
        directory = self.root / 'blank'
        directory.mkdir()
        artifact = directory / 'p.json'
        atomic_json(artifact, {'schema_version': 2, 'empty_part': True, 'blocks': [],
                               'tables': [], 'sections': [], 'extraction': {'warnings': []}})
        part = ExtractionPart('p', 0, PartStatus.COMPLETED, 1, 1, artifact.name, checksum(artifact))
        manifest = ExtractionManifest('doc', 'hash', 'config', 'page', (part,))
        with self.assertRaisesRegex(ValueError, 'no supported text/table'):
            assemble(directory, manifest, 'fake')

    @unittest.skipUnless(importlib.util.find_spec('pypdf'), 'pypdf runtime dependency not installed')
    async def test_pdf_planner_and_fragment_writer_use_exact_ranges(self):
        from pypdf import PdfReader, PdfWriter
        source = self.root / 'small.pdf'
        writer = PdfWriter()
        for width in (100, 200, 300):
            writer.add_blank_page(width=width, height=100)
        with source.open('wb') as stream:
            writer.write(stream)
        partitioner = SourcePartitioner(pdf_pages=2)
        unit, parts = partitioner.plan(source, self.root)
        self.assertEqual(unit, 'page')
        self.assertEqual([(part.source_start, part.source_end) for part in parts], [(1, 2), (3, 3)])
        output = self.root / 'fragment.pdf'
        partitioner.materialize(source, parts[1], output)
        fragment = PdfReader(output)
        self.assertEqual(len(fragment.pages), 1)
        self.assertEqual(float(fragment.pages[0].mediabox.width), 300)


if __name__ == '__main__':
    unittest.main()
