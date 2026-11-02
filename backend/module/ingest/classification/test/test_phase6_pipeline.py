"""Offline integration tests over real planners/use cases and injected providers."""
from copy import deepcopy
from dataclasses import asdict
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import AsyncMock, patch
from contextlib import asynccontextmanager
import asyncio
from uuid import uuid4

from shared.ingestion.document import (
    BlockKind, ContentBlock, ExtractedDocumentV2, ExtractedTable,
    ExtractionMetadata, SourceLocation, StructureQuality, TableCell,
)
from module.ingest.classification.application.use_cases.classify_batch import ClassifyBatchUseCase
from module.ingest.classification.domain.contracts.chunk_reader import ChunkForClassification, ChunkReader
from module.ingest.classification.domain.contracts.classification_engine import ClassificationResult
from module.ingest.classification.domain.contracts.classification_task_repository import ClassificationLeaseLostError
from module.ingest.classification.domain.entities.classification_task import ClassificationTask
from module.ingest.classification.domain.entities.document_context import (
    DocumentContext, DocumentContextDocumentType, DocumentContextTopic, DocumentContextHead,
)
from module.ingest.classification.domain.enums.task_status import TaskStatus
from module.ingest.classification.infrastructure.engine.document_context_payload import DocumentContextPayloadReader
from module.ingest.classification.infrastructure.engine.llm_document_structure_analyzer import LLMDocumentStructureAnalyzer
from module.ingest.chunking.domain.contracts.chunking_engine import ExtractedDocument
from module.ingest.chunking.infrastructure.engine.streaming_chunking_engine import StreamingChunkingEngine
from module.ingest.knowledge.application.services.knowledge_writer import KnowledgeWriter


def context():
    return DocumentContext(DocumentContextDocumentType('manual'), DocumentContextTopic('maintenance'),
                           DocumentContextHead(type='product', code='machine'))


def response(content='Information'):
    return {'sensitivity': {'level': 1, 'description': 'Test'}, 'objects': [],
            'information_types': [], 'information_fields': [],
            'information': [{'summary': content, 'data': {'value': content}}]}


class MemoryKnowledge:
    def __init__(self):
        self.information = []

    async def upsert_document_type(self, entity):
        entity.id = uuid4()
        return entity

    upsert_topic = upsert_document_type

    async def upsert_information_types(self, entities):
        return entities

    upsert_information_fields = upsert_information_types

    async def upsert_information(self, entity, source_identity):
        self.information.append(entity)
        return entity


class Pages(ChunkReader):
    def __init__(self, chunks, persisted):
        self.chunks = chunks
        self.persisted = persisted
        self.sizes = []

    async def list_by_batch_id(self, batch_id):
        raise AssertionError('Production path must not load the complete batch')

    async def iter_by_batch_id(self, batch_id, *, page_size=32):
        for start in range(0, len(self.chunks), page_size):
            if len(self.persisted) != start:
                raise AssertionError('Page must be persisted before loading the next one')
            values = self.chunks[start:start + page_size]
            self.sizes.append(len(values))
            yield values


class PipelineTests(unittest.IsolatedAsyncioTestCase):
    def make_use_case(self, chunks, *, owner=None, engine=None):
        task = ClassificationTask(uuid4(), uuid4(), uuid4(), uuid4(), TaskStatus.PROCESSING,
                                  1, owner, None, None, None, None, None)
        knowledge = MemoryKnowledge()
        repository = SimpleNamespace(get_by_id=AsyncMock(return_value=task), update=AsyncMock(),
                                     renew_lease=AsyncMock(return_value=True))
        async def classify(page, document_context):
            return [ClassificationResult(chunk.id, 'fake-model', response(chunk.content)) for chunk in page]
        pages = Pages(chunks, knowledge.information)
        use_case = ClassifyBatchUseCase(
            task_repository=repository, chunk_reader=pages,
            document_structure_analyzer=SimpleNamespace(analyze=AsyncMock(return_value=context())),
            classification_engine=engine or SimpleNamespace(classify_batch=AsyncMock(side_effect=classify)),
            classification_repository=SimpleNamespace(upsert_many=AsyncMock()),
            batch_finalizer=SimpleNamespace(complete_classification=AsyncMock(
                return_value=SimpleNamespace(dispatch_index=False)), dispatch_index=AsyncMock()),
            knowledge_writer=KnowledgeWriter(knowledge),
            ingestion_config_service=SimpleNamespace(get_job=AsyncMock(return_value=SimpleNamespace(knowledge_space_id=uuid4()))),
            uow=SimpleNamespace(commit=AsyncMock(), rollback=AsyncMock()), page_size=2,
        )
        return use_case, task, knowledge, pages

    async def test_multiple_pages_preserve_information_context_and_provenance(self):
        chunks = [ChunkForClassification(uuid4(), f'Original {i}', {
            'schema_version': 2, 'source_block_ids': [f'b{i}'],
            'text_spans': [{'block_id': f'b{i}', 'start': 0, 'end': 10}],
        }) for i in range(5)]
        use_case, task, knowledge, pages = self.make_use_case(chunks)
        await use_case.execute(task.id)
        self.assertEqual(pages.sizes, [2, 2, 1])
        self.assertEqual(task.status, TaskStatus.COMPLETED)
        self.assertEqual(len(knowledge.information), 5)
        for chunk, info in zip(chunks, knowledge.information):
            self.assertEqual(info.source_refs[0]['chunk_provenance'], chunk.metadata)
            self.assertEqual(info.metadata['document_context']['head']['code'], 'machine')
            self.assertEqual(info.topic_refs[0]['code'], 'maintenance')
            self.assertEqual(info.data, {'value': chunk.content})
        use_case.document_structure_analyzer.analyze.assert_awaited_once()
        original = deepcopy(knowledge.information[0].source_refs[0]['chunk_provenance'])
        chunks[0].metadata['source_block_ids'].append('Later mutation')
        self.assertEqual(knowledge.information[0].source_refs[0]['chunk_provenance'], original)

    async def test_empty_batch_rolls_back_without_completion(self):
        use_case, task, _, _ = self.make_use_case([])
        with self.assertRaisesRegex(ValueError, 'empty chunk batch'):
            await use_case.execute(task.id)
        use_case.uow.rollback.assert_awaited_once()
        use_case.batch_finalizer.complete_classification.assert_not_called()
        self.assertEqual(task.status, TaskStatus.READY)

    async def test_missing_duplicate_or_foreign_results_cannot_complete(self):
        for mode in ('missing', 'duplicate', 'foreign'):
            chunks = [ChunkForClassification(uuid4(), 'Text', {}) for _ in range(2)]
            async def classify(page, document_context):
                ids = {'missing': [page[0].id], 'duplicate': [page[0].id, page[0].id],
                       'foreign': [page[0].id, uuid4()]}[mode]
                return [ClassificationResult(value, 'model', response()) for value in ids]
            engine = SimpleNamespace(classify_batch=AsyncMock(side_effect=classify))
            use_case, task, knowledge, _ = self.make_use_case(chunks, engine=engine)
            with self.subTest(mode=mode), self.assertRaisesRegex(ValueError, 'exactly one'):
                await use_case.execute(task.id)
            self.assertEqual(knowledge.information, [])
            use_case.batch_finalizer.complete_classification.assert_not_called()

    async def test_late_page_failure_rolls_back_the_unit_of_work(self):
        chunks = [ChunkForClassification(uuid4(), 'Text', {}) for _ in range(3)]
        use_case, task, _, _ = self.make_use_case(chunks)
        calls = 0
        async def classify(page, document_context):
            nonlocal calls
            calls += 1
            if calls == 2:
                raise RuntimeError('Provider failed')
            return [ClassificationResult(c.id, 'model', response()) for c in page]
        use_case.classification_engine.classify_batch.side_effect = classify
        with self.assertRaisesRegex(RuntimeError, 'Provider failed'):
            await use_case.execute(task.id)
        use_case.uow.rollback.assert_awaited_once()
        use_case.batch_finalizer.complete_classification.assert_not_called()

    async def test_lost_owner_rolls_back_without_resetting_task(self):
        use_case, task, _, _ = self.make_use_case([ChunkForClassification(uuid4(), 'Text', {})], owner='owner')
        use_case.task_repository.renew_lease.return_value = False
        with self.assertRaises(ClassificationLeaseLostError):
            await use_case.execute(task.id)
        use_case.uow.commit.assert_not_called()
        use_case.task_repository.update.assert_not_called()

    async def test_roundtrip_flat_v2_table_through_chunking_and_knowledge(self):
        location = SourceLocation(page_number=1, part_id='p1')
        table = ExtractedTable('t', 2, 1, (TableCell(0, 0, 'Voltage'), TableCell(1, 0, '220 V')),
                               location, header_rows=(0,))
        doc = ExtractedDocumentV2('doc', 'Manual', ExtractionMetadata('test', '1', StructureQuality.FLAT),
            (ContentBlock('b0', 0, BlockKind.PARAGRAPH, location, text='Machine data'),
             ContentBlock('b1', 1, BlockKind.TABLE, location, table_id='t')), (table,))
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'input.json'
            path.write_text(json.dumps(asdict(doc)), encoding='utf8')
            built = list(StreamingChunkingEngine(max_chunk_tokens=1800).chunk(ExtractedDocument(uuid4(), path)))
        chunks = [ChunkForClassification(uuid4(), chunk.content, chunk.metadata) for chunk in built]
        use_case, task, knowledge, _ = self.make_use_case(chunks)
        await use_case.execute(task.id)
        table_info = next(info for info in knowledge.information if '220 V' in info.summary)
        self.assertEqual(table_info.source_refs[0]['chunk_provenance']['source_block_ids'], ['b1'])
        self.assertIn('table_slices', table_info.source_refs[0]['chunk_provenance'])

    async def test_streamed_v2_context_analysis_uses_original_table_cells(self):
        value = {'schema_version': 2, 'title': 'Manual', 'blocks': [{'kind': 'table'}],
                 'tables': [{'cells': [{'text': 'Voltage 220 V'}]}]}
        async def content():
            data = json.dumps(value).encode()
            for start in range(0, len(data), 13):
                yield data[start:start + 13]
        asset_reader = SimpleNamespace(open_extracted=AsyncMock(return_value=SimpleNamespace(content=content())))
        gateway = SimpleNamespace(generate=AsyncMock(return_value=SimpleNamespace(
            content=json.dumps({'document_type': {'code': 'manual'}, 'topic': {'code': 'maintenance'}, 'head': {}}),
            model_code='fake-model')))
        analyzer = LLMDocumentStructureAnalyzer(
            asset_reader, SimpleNamespace(get_by_code=AsyncMock(return_value=SimpleNamespace(
                system_prompt='User prompt', configuration={}))), gateway)
        result = await analyzer.analyze(ingestion_job_id=uuid4(), document_id=uuid4())
        self.assertEqual(result.document_type.code, 'manual')
        payload = json.loads(gateway.generate.call_args.kwargs['user_prompt'])
        self.assertIn('220 V', payload['fallback_text'])


class PersistenceTests(unittest.IsolatedAsyncioTestCase):
    async def test_chunk_query_keyset_pages_keep_order_and_metadata(self):
        from sqlalchemy import create_engine
        from module.ingest.chunking.infrastructure.persistence.queries.document_chunk_query import DocumentChunkQuery
        engine = create_engine('sqlite://')
        try:
            with engine.connect() as connection:
                connection.exec_driver_sql('CREATE TABLE document_chunks (id TEXT, batch_id TEXT, chunk_index INTEGER, content TEXT, metadata JSON)')
                batch_id = uuid4()
                for index in (8, 0, 3, 5, 1):
                    connection.exec_driver_sql('INSERT INTO document_chunks VALUES (?,?,?,?,?)',
                        (uuid4().hex, batch_id.hex, index, str(index), json.dumps({'source_block_ids': [str(index)]})))
                connection.exec_driver_sql('INSERT INTO document_chunks VALUES (?,?,?,?,?)',
                    (uuid4().hex, uuid4().hex, 2, 'Other batch', '{}'))
                calls = []
                class Session:
                    async def execute(self, statement):
                        calls.append(statement)
                        return connection.execute(statement)
                pages = [page async for page in DocumentChunkQuery(Session()).iter_by_batch_id(batch_id, page_size=2)]
                self.assertEqual([len(page) for page in pages], [2, 2, 1])
                self.assertEqual([chunk.content for page in pages for chunk in page], ['0', '1', '3', '5', '8'])
                self.assertEqual(pages[-1][0].metadata['source_block_ids'], ['8'])
                self.assertTrue(all(statement._limit_clause.value == 2 for statement in calls))
        finally:
            engine.dispose()

    async def test_classification_and_embedding_leases_reject_expired_or_other_owner(self):
        from sqlalchemy import create_engine
        from module.ingest.classification.infrastructure.persistence.repositories.classification_task_repository_impl import ClassificationTaskRepositoryImpl
        from module.ingest.embedding.infrastructure.persistence.repositories.embedding_task_repository_impl import EmbeddingTaskRepositoryImpl
        for table, repository_class in [('classification_tasks', ClassificationTaskRepositoryImpl), ('embedding_tasks', EmbeddingTaskRepositoryImpl)]:
            with self.subTest(table=table):
                engine = create_engine('sqlite://')
                try:
                    with engine.connect() as connection:
                        connection.exec_driver_sql(f'CREATE TABLE {table} (id TEXT, ingestion_job_id TEXT, status TEXT, claimed_by TEXT, lease_until DATETIME, updated_at DATETIME)')
                        class Session:
                            async def execute(self, statement):
                                return connection.execute(statement)
                        repository = repository_class(Session())
                        task, job = uuid4(), uuid4()
                        now = datetime.now(timezone.utc)
                        connection.exec_driver_sql(f'INSERT INTO {table} VALUES (?,?,?,?,?,?)',
                            (task.hex, job.hex, 'PROCESSING', 'owner',
                             (now + timedelta(minutes=5)).replace(tzinfo=None).isoformat(' '), now.isoformat(' ')))
                        self.assertTrue(await repository.has_unfinished(job))
                        self.assertFalse(await repository.renew_lease(task, claimed_by='other', lease_until=now + timedelta(minutes=10)))
                        self.assertTrue(await repository.renew_lease(task, claimed_by='owner', lease_until=now + timedelta(minutes=10)))
                        connection.exec_driver_sql(f'UPDATE {table} SET lease_until=?',
                            ((now - timedelta(minutes=1)).replace(tzinfo=None).isoformat(' '),))
                        self.assertFalse(await repository.renew_lease(task, claimed_by='owner', lease_until=now + timedelta(minutes=10)))
                        connection.exec_driver_sql(f"UPDATE {table} SET status='COMPLETED'")
                        self.assertFalse(await repository.has_unfinished(job))
                finally:
                    engine.dispose()


class EmbeddingTests(unittest.IsolatedAsyncioTestCase):
    def make_use_case(self, chunks, *, failure=None):
        from module.ingest.embedding.application.use_cases.embed_batch import EmbedBatchUseCase
        from module.ingest.embedding.domain.entities.embedding_task import EmbeddingTask
        from module.ingest.embedding.domain.enums.task_status import TaskStatus as EmbeddingStatus
        from module.ingest.embedding.domain.contracts.embedding_engine import EmbeddingResult
        task = EmbeddingTask(uuid4(), uuid4(), uuid4(), uuid4(), EmbeddingStatus.PROCESSING,
                             1, None, None, None, None, None, None)
        persisted = []
        async def embed(page):
            if failure == 'missing':
                return []
            return [EmbeddingResult(c.id, [1.0, 2.0], 'fake', 3 if failure == 'dimension' else 2,
                                    None, 'success', None) for c in page]
        async def save(rows):
            persisted.extend(rows)
        use_case = EmbedBatchUseCase(
            task_repository=SimpleNamespace(get_by_id=AsyncMock(return_value=task), update=AsyncMock()),
            chunk_reader=Pages(chunks, persisted),
            embedding_engine_resolver=SimpleNamespace(resolve_for_job=AsyncMock(return_value=SimpleNamespace(embed_batch=embed))),
            embedding_repository=SimpleNamespace(upsert_many=AsyncMock(side_effect=save)),
            batch_finalizer=SimpleNamespace(complete_embedding=AsyncMock(return_value=SimpleNamespace(dispatch_index=False))),
            uow=SimpleNamespace(commit=AsyncMock(), rollback=AsyncMock()), page_size=2,
        )
        return use_case, task, persisted

    async def test_embedding_consumes_and_persists_one_page_at_a_time(self):
        use_case, task, persisted = self.make_use_case([ChunkForClassification(uuid4(), 'Text', {}) for _ in range(5)])
        await use_case.execute(task.id)
        self.assertEqual(len(persisted), 5)
        self.assertEqual(use_case.chunk_reader.sizes, [2, 2, 1])
        self.assertEqual(task.status.value, 'COMPLETED')

    async def test_missing_and_invalid_vectors_cannot_complete(self):
        for failure in ('missing', 'dimension'):
            use_case, task, persisted = self.make_use_case([ChunkForClassification(uuid4(), 'Text', {})], failure=failure)
            with self.subTest(failure=failure), self.assertRaises(ValueError):
                await use_case.execute(task.id)
            self.assertEqual(persisted, [])
            use_case.batch_finalizer.complete_embedding.assert_not_called()

    async def test_empty_embedding_batch_fails(self):
        use_case, task, _ = self.make_use_case([])
        with self.assertRaisesRegex(ValueError, 'empty chunk batch'):
            await use_case.execute(task.id)
        use_case.uow.rollback.assert_awaited_once()


class RequestBudgetTests(unittest.IsolatedAsyncioTestCase):
    async def test_complete_prompt_overflow_prevents_provider_call(self):
        from module.ingest.classification.infrastructure.engine.llm_classification_engine import LLMClassificationEngine
        gateway = SimpleNamespace(generate=AsyncMock())
        prompt = SimpleNamespace(system_prompt='Long system rules ' * 100,
            configuration={'ingestion_request_limits': {'context_window_tokens': 1024, 'reserve_output_tokens': 128}})
        engine = LLMClassificationEngine(SimpleNamespace(get_by_code=AsyncMock(return_value=prompt)), gateway)
        with self.assertRaisesRegex(ValueError, 'Complete ingestion model request'):
            await engine.classify_batch([ChunkForClassification(uuid4(), 'Small chunk', {})], context())
        gateway.generate.assert_not_called()

    async def test_limits_are_not_forwarded_as_provider_options(self):
        from module.ingest.classification.infrastructure.engine.llm_classification_engine import LLMClassificationEngine
        prompt = SimpleNamespace(system_prompt='Rules', configuration={
            'temperature': 0, 'ingestion_request_limits': {'context_window_tokens': 10000, 'reserve_output_tokens': 500}})
        gateway = SimpleNamespace(generate=AsyncMock(return_value=SimpleNamespace(
            content=json.dumps(response()), model_code='fake', finish_reason='stop')))
        engine = LLMClassificationEngine(SimpleNamespace(get_by_code=AsyncMock(return_value=prompt)), gateway)
        await engine.classify_batch([ChunkForClassification(uuid4(), 'Original', {'source_block_ids': ['b0']})], context())
        self.assertEqual(gateway.generate.call_args.kwargs['config'], {'temperature': 0})
        payload = json.loads(gateway.generate.call_args.kwargs['user_prompt'])
        self.assertEqual(payload['metadata']['source_block_ids'], ['b0'])

    async def test_output_reservation_covers_configured_provider_maximum(self):
        from module.ingest.classification.application.services.model_request_budget import ModelRequestBudget
        config = {'ingestion_request_limits': {'context_window_tokens': 1000, 'reserve_output_tokens': 100}, 'max_tokens': 800}
        budget = ModelRequestBudget.from_config(config)
        with self.assertRaises(ValueError):
            budget.validate('System', 'Text')


class WorkerTests(unittest.IsolatedAsyncioTestCase):
    def workers(self):
        from workers.ingest.classification_worker import ClassificationWorker
        from workers.ingest.embedding_worker import EmbeddingWorker
        return ClassificationWorker, EmbeddingWorker

    async def test_workers_drain_all_claims_before_acknowledging_job_message(self):
        for worker_class in self.workers():
            with self.subTest(worker=worker_class.__name__):
                job, task_id, document_id = uuid4(), uuid4(), uuid4()
                repository = SimpleNamespace(claim_ready=AsyncMock(side_effect=[
                    [SimpleNamespace(id=task_id, ingestion_job_id=job, document_id=document_id)], []]),
                    has_unfinished=AsyncMock(return_value=False))
                progress = SimpleNamespace(mark_stage_processing=AsyncMock())
                uow = SimpleNamespace(commit=AsyncMock())
                @asynccontextmanager
                async def scope():
                    yield repository, uow, progress
                message = SimpleNamespace(payload={'ingestion_job_id': str(job)}, ack=AsyncMock())
                consumer = SimpleNamespace(receive=AsyncMock(side_effect=[[message], asyncio.CancelledError()]))
                worker = worker_class(consumer, scope, None)
                worker._process = AsyncMock()
                with self.assertRaises(asyncio.CancelledError):
                    await worker.run()
                self.assertEqual(repository.claim_ready.await_count, 2)
                message.ack.assert_awaited_once()
                worker._process.assert_awaited_once_with(task_id)

    async def test_lost_lease_cancels_running_model_work(self):
        for worker_class in self.workers():
            with self.subTest(worker=worker_class.__name__):
                repository = SimpleNamespace(renew_lease=AsyncMock(return_value=False),
                    get_by_id=AsyncMock(return_value=SimpleNamespace(status=TaskStatus.PROCESSING)))
                @asynccontextmanager
                async def scope():
                    yield repository, SimpleNamespace(commit=AsyncMock()), None
                worker = worker_class(None, scope, None, lease_seconds=1)
                cancelled = []
                async def execute(task_id):
                    try:
                        await asyncio.Event().wait()
                    finally:
                        cancelled.append(True)
                with self.assertRaisesRegex(RuntimeError, 'lease was lost'):
                    await worker._execute_with_heartbeat(SimpleNamespace(execute=execute), uuid4())
                self.assertEqual(cancelled, [True])


class ContextPayloadTests(unittest.TestCase):
    def read(self, value, **options):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'input.json'
            path.write_text(json.dumps(value), encoding='utf8')
            return DocumentContextPayloadReader(**options).read(path)

    def test_v2_without_legacy_sections_and_bounded_headings(self):
        value = {'blocks': [{'text': 'Body'}], 'sections': [
            {'title': 'Heading ' * 100, 'level': 1} for _ in range(200)], 'schema_version': 2, 'title': 'Manual'}
        result = self.read(value, max_headings=3, max_heading_chars=20)
        self.assertEqual(len(result['sections']), 3)
        self.assertTrue(all(len(s['title']) <= 20 for s in result['sections']))
        self.assertEqual(result['title'], 'Manual')

    def test_flat_v2_table_only_produces_context_text(self):
        result = self.read({'schema_version': 2, 'blocks': [{'kind': 'table'}],
                            'tables': [{'cells': [{'text': 'Voltage'}, {'text': '220 V'}]}]})
        payload = LLMDocumentStructureAnalyzer._build_document_payload(result)
        self.assertIn('220 V', payload['fallback_text'])
        self.assertTrue(payload['content_sample_is_partial'])

    def test_text_sample_is_bounded(self):
        result = self.read({'schema_version': 2, 'blocks': [{'text': 'x' * 10000} for _ in range(20)]})
        self.assertEqual(len(result['content']), 4000)
        self.assertEqual(result['block_count'], 20)

    def test_v2_does_not_use_full_document_json_load(self):
        with patch('json.load', side_effect=AssertionError('Full JSON loading forbidden')):
            self.read({'schema_version': 2, 'blocks': [{'text': 'Body'}]})

    def test_legacy_tree_is_compatible(self):
        value = {'title': 'Legacy', 'sections': [{'title': 'Heading', 'children': []}]}
        self.assertEqual(self.read(value), value)

    def test_unknown_version_and_empty_v2_fail(self):
        for value in ({'schema_version': 3}, {'schema_version': True}, {'schema_version': 2, 'blocks': []}):
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.read(value)
