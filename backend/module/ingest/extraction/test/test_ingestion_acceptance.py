"""Final offline acceptance; no large-source extraction or remote providers."""
from dataclasses import asdict
import json
from pathlib import Path
import random
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import AsyncMock, patch
from uuid import uuid4
from zipfile import ZipFile

from shared.ingestion.document import BlockKind, ContentBlock, ExtractedDocumentV2, ExtractionMetadata, SourceLocation, StructureQuality
from module.ingest.extraction.infrastructure.multipart.engine import MultipartExtractionEngine
from module.ingest.extraction.infrastructure.multipart.partitioner import SourcePartitioner
from module.ingest.extraction.infrastructure.multipart.process_executor import ProcessPartExecutor
from module.ingest.chunking.domain.contracts.chunking_engine import Chunk, ExtractedDocument
from module.ingest.chunking.infrastructure.engine.streaming_chunking_engine import StreamingChunkingEngine
from module.ingest.chunking.application.services.chunk_budget import ChunkBudget
from module.ingest.classification.application.use_cases.classify_batch import ClassifyBatchUseCase
from module.ingest.classification.domain.contracts.chunk_reader import ChunkForClassification
from module.ingest.classification.domain.contracts.classification_engine import ClassificationResult
from module.ingest.classification.domain.entities.classification_task import ClassificationTask
from module.ingest.classification.domain.enums.task_status import TaskStatus
from module.ingest.classification.test.test_phase6_pipeline import MemoryKnowledge, Pages, context, response
from module.ingest.knowledge.application.services.knowledge_writer import KnowledgeWriter
from bootstrap.ingestion_verification import create_ingestion_verifier
from tools.ingestion_verification.runner import VerificationRunner


def docx_fixture(path):
    with ZipFile(path, 'w') as archive:
        archive.writestr('word/document.xml', '''
        <w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body>
          <w:p><w:pPr><w:pStyle w:val="UnrecognizedFancyStyle"/></w:pPr><w:r><w:t>Unnumbered introduction</w:t></w:r></w:p>
          <w:p><w:r><w:t>Voltage data follows.</w:t></w:r></w:p>
          <w:tbl><w:tblGrid><w:gridCol/><w:gridCol/></w:tblGrid>
            <w:tr><w:trPr><w:tblHeader/></w:trPr><w:tc><w:p><w:r><w:t>Device</w:t></w:r></w:p></w:tc>
              <w:tc><w:p><w:r><w:t>Voltage</w:t></w:r></w:p></w:tc></w:tr>
            <w:tr><w:tc><w:p><w:r><w:t>Machine A</w:t></w:r></w:p></w:tc>
              <w:tc><w:p><w:r><w:t>220 V</w:t></w:r></w:p></w:tc></w:tr>
          </w:tbl>
          <w:p><w:r><w:t>Final maintenance instructions.</w:t></w:r></w:p>
        </w:body></w:document>''')
        archive.writestr('docProps/core.xml', '''
        <cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties"
          xmlns:dc="http://purl.org/dc/elements/1.1/"><dc:title>Electrical maintenance</dc:title></cp:coreProperties>''')


class IngestionAcceptanceTests(unittest.IsolatedAsyncioTestCase):
    async def test_real_native_parts_reach_knowledge_without_heading_dependency(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / 'input.docx'
            docx_fixture(source)
            result = await MultipartExtractionEngine('docling', {'extraction_runtime': {
                'docx_blocks_per_part': 2}}, cache_root=root / 'cache').extract(source)
            payload = json.loads(result.content_file.read_text(encoding='utf8'))
            self.assertEqual(payload['title'], 'Electrical maintenance')
            self.assertEqual(payload['extraction']['structure_quality'], 'flat')
            self.assertEqual(payload['extraction']['engine_version'], '2')
            built = list(StreamingChunkingEngine().chunk(ExtractedDocument(uuid4(), result.content_file)))
            chunks = [ChunkForClassification(uuid4(), value.content, value.metadata) for value in built]
            knowledge = MemoryKnowledge()
            task = ClassificationTask(uuid4(), uuid4(), uuid4(), uuid4(), TaskStatus.PROCESSING,
                                      1, None, None, None, None, None, None)
            async def classify(page, document_context):
                return [ClassificationResult(value.id, 'offline-fake', response(value.content)) for value in page]
            use_case = ClassifyBatchUseCase(
                task_repository=SimpleNamespace(get_by_id=AsyncMock(return_value=task), update=AsyncMock()),
                chunk_reader=Pages(chunks, knowledge.information),
                document_structure_analyzer=SimpleNamespace(analyze=AsyncMock(return_value=context())),
                classification_engine=SimpleNamespace(classify_batch=classify),
                classification_repository=SimpleNamespace(upsert_many=AsyncMock()),
                batch_finalizer=SimpleNamespace(complete_classification=AsyncMock(return_value=SimpleNamespace(dispatch_index=False))),
                knowledge_writer=KnowledgeWriter(knowledge),
                ingestion_config_service=SimpleNamespace(get_job=AsyncMock(return_value=SimpleNamespace(knowledge_space_id=uuid4()))),
                uow=SimpleNamespace(commit=AsyncMock(), rollback=AsyncMock()), page_size=1,
            )
            await use_case.execute(task.id)
            text = '\n'.join(info.summary for info in knowledge.information)
            for expected in ('Unnumbered introduction', '220 V', 'Final maintenance instructions.'):
                self.assertIn(expected, text)
            self.assertEqual(task.status, TaskStatus.COMPLETED)
            self.assertTrue(all(info.source_refs[0]['chunk_provenance']['part_ids'] for info in knowledge.information))

    async def test_verifier_cache_replay_has_identical_digest_and_no_reextraction(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / 'input.docx'
            docx_fixture(source)
            runner = create_ingestion_verifier(engine='docling', cache_root=root / 'cache', blocks_per_part=2)
            first = await runner.run(source)
            with patch.object(ProcessPartExecutor, 'execute', side_effect=AssertionError('Cached parts must be reused')):
                second = await runner.run(source)
            self.assertEqual(first.source_sha256, second.source_sha256)
            self.assertEqual(first.chunk_sha256, second.chunk_sha256)
            self.assertGreater(first.chunk_count, 0)
            self.assertGreater(first.parent_python_peak_bytes, 0)

    async def test_partial_or_empty_chunk_stream_never_produces_a_success_report(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / 'input.json'
            source.write_text('{}', encoding='utf8')
            async def extract(path):
                return path
            async def failed(path):
                yield Chunk(0, None, 'Partial', {})
                raise ValueError('Coverage incomplete')
            async def empty(path):
                if False:
                    yield
            for chunks in (failed, empty):
                with self.subTest(stream=chunks.__name__), self.assertRaises(ValueError):
                    await VerificationRunner(extract=extract, chunks=chunks).run(source)

    async def test_verifier_closes_stream_on_invalid_order(self):
        closed = []
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / 'input.json'
            source.write_text('{}', encoding='utf8')
            async def extract(path):
                return path
            async def chunks(path):
                try:
                    yield Chunk(5, None, 'Invalid sequence', {})
                finally:
                    closed.append(True)
            with self.assertRaises(ValueError):
                await VerificationRunner(extract=extract, chunks=chunks).run(source)
        self.assertEqual(closed, [True])

    async def test_verifier_rejects_a_source_modified_during_execution(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / 'input.json'
            source.write_text('Original', encoding='utf8')
            async def extract(path):
                path.write_text('Changed', encoding='utf8')
                return path
            async def chunks(path):
                yield Chunk(0, None, 'Text', {})
            with self.assertRaisesRegex(ValueError, 'Source changed'):
                await VerificationRunner(extract=extract, chunks=chunks).run(source)

    async def test_cli_existing_report_and_provider_opt_in_are_checked_before_execution(self):
        from scripts.verify_ingestion import parser, verify
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / 'input.pdf'
            source.write_bytes(b'Not executed')
            with self.assertRaisesRegex(ValueError, 'allow-provider'):
                await verify(parser().parse_args([str(source)]))
            report = root / 'report.json'
            report.write_text('Keep existing report', encoding='utf8')
            with self.assertRaisesRegex(ValueError, 'already exists'):
                await verify(parser().parse_args([str(source), '--report', str(report)]))
            self.assertEqual(report.read_text(encoding='utf8'), 'Keep existing report')

    async def test_cli_json_artifact_emits_new_report_and_checks_repeat_digest(self):
        from scripts.verify_ingestion import parser, verify
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / 'extracted.json'
            value = ExtractedDocumentV2('doc', 'Flat', ExtractionMetadata('test', '1', StructureQuality.FLAT),
                (ContentBlock('b0', 0, BlockKind.PARAGRAPH, SourceLocation(), text='Original source text'),))
            source.write_text(json.dumps(asdict(value)), encoding='utf8')
            report = root / 'report.json'
            result = json.loads(await verify(parser().parse_args([
                str(source), '--report', str(report), '--cache-dir', str(root / 'cache'), '--repeat', '2'])))
            self.assertEqual(result['status'], 'passed')
            self.assertEqual(result['runs'][0]['chunk_sha256'], result['runs'][1]['chunk_sha256'])
            self.assertEqual(json.loads(report.read_text(encoding='utf8')), result)


class ScalePlanningTests(unittest.TestCase):
    def test_page_plans_through_500_use_bounded_exact_ranges_without_large_extraction(self):
        # Only the page-count interface is simulated: no large PDF is created/read.
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / 'page-count-only.pdf'
            source.write_bytes(b'planner-test')
            for count in (100, 200, 300, 500):
                with self.subTest(count=count), patch('pypdf.PdfReader', return_value=SimpleNamespace(is_encrypted=False, pages=range(count))):
                    unit, parts = SourcePartitioner(pdf_pages=20).plan(source, Path(directory))
                    self.assertEqual(unit, 'page')
                    self.assertEqual(len(parts), count // 20)
                    self.assertEqual([page for part in parts for page in range(part.source_start, part.source_end + 1)], list(range(1, count + 1)))
                    self.assertTrue(all(part.source_end - part.source_start + 1 <= 20 for part in parts))

    def test_varied_flat_unicode_text_is_recoverable_from_original_offsets(self):
        generator = random.Random(7)
        location = SourceLocation(part_id='p1')
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'input.json'
            for iteration in range(12):
                originals = {f'b{i}': ''.join(generator.choice(['A', ' ', '\n', '\u0111', '\u96fb', '\U0001f600'])
                    for _ in range(generator.randint(20, 300))) + 'end' for i in range(7)}
                value = ExtractedDocumentV2('doc', 'Flat', ExtractionMetadata('test', '1', StructureQuality.FLAT),
                    tuple(ContentBlock(key, index, BlockKind.PARAGRAPH, location, text=text)
                          for index, (key, text) in enumerate(originals.items())))
                path.write_text(json.dumps(asdict(value)), encoding='utf8')
                chunks = list(StreamingChunkingEngine(max_chunk_tokens=1200).chunk(ExtractedDocument(uuid4(), path)))
                recovered = {key: '' for key in originals}
                for chunk in chunks:
                    self.assertTrue(ChunkBudget(1200).fits(chunk.content, chunk.metadata))
                    for span in chunk.metadata['text_spans']:
                        self.assertEqual(span['start'], len(recovered[span['block_id']]))
                        recovered[span['block_id']] += chunk.content[span['content_start']:span['content_end']]
                self.assertEqual(recovered, originals)
