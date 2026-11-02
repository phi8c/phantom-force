import asyncio
from datetime import datetime, timezone
import importlib.util
import io
import json
from pathlib import Path
import shutil
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import AsyncMock, patch
from uuid import uuid4

from module.structured_data.application.services import StructuredBuildService, StructuredQueryService
from module.structured_data.application.query_compiler import QueryRejected
from module.structured_data.infrastructure.workbook import XlsxWorkbookBuilder, checksum
from module.structured_data.infrastructure.query_engine import DuckDbQueryEngine
from module.structured_data.infrastructure.catalog import SqlDatasetCatalog, decode_dataset, encode_dataset
from module.structured_data.infrastructure.artifacts import FileStorageArtifacts
from module.structured_data.infrastructure.cache import CachedArtifacts


class MemoryArtifacts:
    def __init__(self):
        self.files = {}
    async def upload(self,path,source,content_type):
        self.files[path] = source.read_bytes()
    async def download(self,path,destination,expected_checksum):
        destination.write_bytes(self.files[path])
        if checksum(destination) != expected_checksum:
            raise ValueError('Checksum mismatch')


class MemoryCatalog:
    def __init__(self):
        self.datasets = []
    async def ensure_ready(self):
        pass
    async def publish(self,space,document,datasets,embeddings,**kwargs):
        self.datasets = datasets
    async def has_datasets(self,space):
        return any(d.knowledge_space_id == space for d in self.datasets)
    async def search(self,space,vector,limit=4):
        return [d for d in self.datasets if d.knowledge_space_id == space]


@unittest.skipUnless(importlib.util.find_spec('duckdb') and importlib.util.find_spec('pyarrow'),
                     'Install backend/requirements-structured-data.txt')
class StructuredIntegrationTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        from openpyxl import Workbook
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.source = self.root/'source.xlsx'
        workbook = Workbook()
        workbook.active.title = 'Sales'
        for row in [['Department','Amount'],['IT',10],['HR',5]]: workbook.active.append(row)
        workbook.save(self.source)
        workbook.close()
        self.space,self.document,self.job_id = uuid4(),uuid4(),uuid4()
        self.catalog,self.artifacts = MemoryCatalog(),MemoryArtifacts()
        self.embedder = SimpleNamespace(embed_texts=AsyncMock(side_effect=lambda texts:[[1.,0.] for _ in texts]))
        self.embedder_factory = AsyncMock(return_value=self.embedder)
        self.build_service = StructuredBuildService(builder=XlsxWorkbookBuilder(),catalog=self.catalog,artifacts=self.artifacts,
            config_service=SimpleNamespace(get_config=AsyncMock(return_value=(
                SimpleNamespace(knowledge_space_id=self.space,created_at=datetime.now(timezone.utc)),
                SimpleNamespace(configuration={})))),embedder_factory=self.embedder_factory)

    def tearDown(self):
        self.temp.cleanup()

    async def build(self):
        return await self.build_service.build(source=self.source,file_name='statistics.xlsx',document_id=self.document,ingestion_job_id=self.job_id)

    def query_service(self,planner):
        return StructuredQueryService(catalog=self.catalog,artifacts=self.artifacts,planner=planner,
                                      engine=DuckDbQueryEngine(),embedder_factory=self.embedder_factory)

    async def test_build_publishes_catalog_and_parquet_but_not_row_knowledge(self):
        payload = await self.build()
        from module.ingest.extraction.infrastructure.normalization.document_codec import decode_document
        decoded = decode_document(payload)
        self.assertEqual(len(decoded.blocks),1)
        self.assertIn('DATASET CATALOG ONLY',decoded.blocks[0].text)
        self.assertEqual(self.catalog.datasets[0].row_count,2)
        self.assertTrue(self.artifacts.files[self.catalog.datasets[0].parquet_path].startswith(b'PAR1'))
        self.assertNotIn('"rows":',decoded.blocks[0].text)
        self.assertEqual(self.embedder_factory.call_args.args,(self.space,))

    async def test_full_build_query_chat_path_returns_computed_rows_and_chart(self):
        await self.build()
        dataset = self.catalog.datasets[0]
        plan = {'dataset_id':str(dataset.id),'select':[{'column':'department','alias':'department'},
            {'column':'amount','aggregate':'sum','alias':'total'}],'order_by':[{'column':'department'}],
            'chart':{'type':'bar','x':'department','y':['total']}}
        planner = SimpleNamespace(plan=AsyncMock(return_value=plan))
        service = self.query_service(planner)
        from module.chats.chat.application.services.chat_service import ChatService
        from module.chats.chat.application.dtos.request.chat_request import ChatRequest
        gateway = SimpleNamespace(generate=AsyncMock(return_value=SimpleNamespace(content='IT: 10, HR: 5.')))
        analyzer = SimpleNamespace(analyze=AsyncMock())
        chat = ChatService(query_analyzer=analyzer,navigation_service=None,
            prompt_provider=SimpleNamespace(get_by_code=AsyncMock(return_value=SimpleNamespace(system_prompt='Answer',configuration={}))),
            llm_gateway=gateway,structured_reader=service)
        response = await chat.chat(ChatRequest(self.space,'Draw revenue by department'))
        self.assertEqual(response.intent,'STRUCTURED')
        self.assertEqual(response.structured_results[0]['rows'],(('HR',5),('IT',10)))
        self.assertEqual(response.structured_results[0]['chart']['type'],'bar')
        analyzer.analyze.assert_not_called()
        payload = json.loads(gateway.generate.call_args.kwargs['user_prompt'])
        self.assertEqual(payload['information'][0]['data']['rows'],[['HR',5],['IT',10]])

    async def test_no_datasets_skips_all_model_embedding_work(self):
        planner = SimpleNamespace(plan=AsyncMock())
        result = await self.query_service(planner).query(knowledge_space_id=self.space,question='Question')
        self.assertIsNone(result)
        planner.plan.assert_not_called()
        self.embedder_factory.assert_not_called()

    async def test_irrelevant_question_falls_back_without_download(self):
        await self.build()
        self.artifacts.download = AsyncMock()
        result = await self.query_service(SimpleNamespace(plan=AsyncMock(return_value=None))).query(
            knowledge_space_id=self.space,question='Unrelated PDF question')
        self.assertIsNone(result)
        self.artifacts.download.assert_not_called()

    async def test_invalid_plan_gets_one_validated_correction_attempt(self):
        await self.build()
        identity = str(self.catalog.datasets[0].id)
        planner = SimpleNamespace(plan=AsyncMock(side_effect=[{'dataset_id':identity,'sql':'DROP TABLE x'},
            {'dataset_id':identity,'select':[{'column':'amount','aggregate':'sum','alias':'total'}]}]))
        result = await self.query_service(planner).query(knowledge_space_id=self.space,question='Total')
        self.assertEqual(result.rows,((15,),))
        self.assertEqual(planner.plan.await_count,2)
        self.assertIn('raw SQL',planner.plan.call_args.kwargs['feedback'])

    async def test_invalid_planner_json_is_corrected_without_text_fallback(self):
        from module.structured_data.infrastructure.planner import LLMStructuredPlanner
        await self.build()
        identity = str(self.catalog.datasets[0].id)
        valid = {'applicable':True,'plan':{'dataset_id':identity,
            'select':[{'column':'amount','aggregate':'sum','alias':'total'}]}}
        gateway = SimpleNamespace(generate=AsyncMock(side_effect=[
            SimpleNamespace(content='broken JSON'),SimpleNamespace(content=json.dumps(valid))]))
        result = await self.query_service(LLMStructuredPlanner(gateway=gateway)).query(
            knowledge_space_id=self.space,question='Total')
        self.assertEqual(result.rows,((15,),))
        self.assertEqual(gateway.generate.await_count,2)
        self.assertIn('valid JSON',gateway.generate.call_args.kwargs['user_prompt'])

    async def test_other_space_cannot_retrieve_catalog_or_records(self):
        await self.build()
        planner = SimpleNamespace(plan=AsyncMock())
        self.assertIsNone(await self.query_service(planner).query(knowledge_space_id=uuid4(),question='Total'))
        planner.plan.assert_not_called()

    async def test_embedding_failure_does_not_publish_partial_catalog(self):
        self.embedder.embed_texts.side_effect = lambda texts: []
        with self.assertRaisesRegex(ValueError,'incomplete'):
            await self.build()
        self.assertEqual(self.catalog.datasets,[])

    async def test_extraction_use_case_routes_xlsx_before_text_engine(self):
        from module.ingest.extraction.application.use_cases.extract_document import ExtractDocumentUseCase
        from module.ingest.extraction.domain.entities.extraction_task import ExtractionTask
        from module.ingest.extraction.domain.enums.task_status import TaskStatus
        task = ExtractionTask(uuid4(),self.job_id,self.document,TaskStatus.PROCESSING,1,None,None,None,None,None,None)
        asset_id = uuid4()
        asset = SimpleNamespace(id=asset_id,document_id=self.document,asset_type='EXTRACTED',
            content_type='application/vnd.phantom.structured-catalog+json',
            storage_path=ExtractDocumentUseCase._build_storage_path(ingestion_job_id=self.job_id,document_id=self.document))
        async def content():
            yield self.source.read_bytes()
        async def upload(**kwargs):
            data = b''.join([part async for part in kwargs['content']])
            self.assertEqual(json.loads(data)['structured_dataset_ids'],[str(d.id) for d in self.catalog.datasets])
            return SimpleNamespace(path=kwargs['path'],provider_id=uuid4(),content_type=kwargs['content_type'],size_bytes=len(data))
        repository = SimpleNamespace(get_by_document_type_and_path=AsyncMock(return_value=None),create=AsyncMock(return_value=asset))
        resolver = SimpleNamespace(resolve_for_job=AsyncMock(side_effect=AssertionError('XLSX must not reach PDF/DOCX engines')))
        scheduler = SimpleNamespace(ensure_ready_task=AsyncMock(),dispatch_job=AsyncMock())
        progress = SimpleNamespace(mark_stage_completed=AsyncMock(),mark_stage_skipped=AsyncMock())
        use_case = ExtractDocumentUseCase(
            task_repository=SimpleNamespace(get_by_id=AsyncMock(return_value=task),update=AsyncMock()),
            source_asset_reader=SimpleNamespace(open_source=AsyncMock(return_value=SimpleNamespace(
                file_name='statistics.xlsx',content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                size_bytes=self.source.stat().st_size,content=content()))),
            extraction_engine_resolver=resolver,object_storage=SimpleNamespace(upload_stream=upload),
            storage_asset_repository=repository,chunking_task_scheduler=scheduler,
            uow=SimpleNamespace(commit=AsyncMock(),rollback=AsyncMock()),structured_builder=self.build_service,
            orchestration_progress_service=progress)
        with patch('sys.stdout',io.StringIO()):
            await use_case.execute(task.id)
        self.assertEqual(task.status,TaskStatus.COMPLETED)
        resolver.resolve_for_job.assert_not_called()
        scheduler.ensure_ready_task.assert_not_called()
        scheduler.dispatch_job.assert_not_called()
        self.assertEqual({call.kwargs['stage'].value for call in progress.mark_stage_skipped.call_args_list},
                         {'CHUNKING','CLASSIFICATION'})
        self.assertEqual({call.kwargs['stage'].value for call in progress.mark_stage_completed.call_args_list},
                         {'EXTRACTION','EMBEDDING','INDEXING'})
        self.assertTrue(self.catalog.datasets)

    async def test_catalog_codec_round_trips_provenance_and_schema(self):
        await self.build()
        original = self.catalog.datasets[0]
        decoded = decode_dataset(json.loads(json.dumps(encode_dataset(original))))
        self.assertEqual(decoded,original)


class ArtifactTests(unittest.IsolatedAsyncioTestCase):
    async def test_cache_reuses_verified_bytes_and_repairs_corruption(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            original = root/'original'; original.write_bytes(b'PAR1 immutable artifact')
            calls = []
            class Delegate:
                async def download(self,path,destination,expected_checksum):
                    calls.append(path)
                    shutil.copyfile(original,destination)
            cache = CachedArtifacts(Delegate(),root/'cache')
            identity = checksum(original)
            await cache.download('structured/space/data.parquet',root/'a',identity)
            await cache.download('structured/space/data.parquet',root/'b',identity)
            self.assertEqual(len(calls),1)
            self.assertEqual((root/'b').read_bytes(),original.read_bytes())
            next((root/'cache').glob('*.parquet')).write_bytes(b'Corrupt')
            await cache.download('structured/space/data.parquet',root/'c',identity)
            self.assertEqual(len(calls),2)
            self.assertEqual((root/'c').read_bytes(),original.read_bytes())

    async def test_download_checksum_and_path_are_verified(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root/'original'; source.write_bytes(b'PAR1 test artifact')
            adapter = FileStorageArtifacts(SimpleNamespace(download=AsyncMock(return_value=source.read_bytes())))
            destination = root/'download'
            await adapter.download('structured/space/data.parquet',destination,checksum(source))
            self.assertEqual(source.read_bytes(),destination.read_bytes())
            with self.assertRaisesRegex(ValueError,'checksum'):
                await adapter.download('structured/space/data.parquet',destination,'wrong')
            self.assertFalse(destination.exists())
            for path in ('../secret','https://example.com/file','structured/../secret'):
                with self.subTest(path=path),self.assertRaises(ValueError):
                    adapter.validate_path(path)


class CatalogSQLTests(unittest.IsolatedAsyncioTestCase):
    async def test_missing_migration_preserves_text_chat_and_rejects_xlsx_write(self):
        session = SimpleNamespace(execute=AsyncMock(return_value=SimpleNamespace(scalar_one=lambda:False)))
        catalog = SqlDatasetCatalog(session)
        self.assertFalse(await catalog.has_datasets(uuid4()))
        with self.assertRaisesRegex(ValueError,'create_structured_datasets.sql'):
            await catalog.publish(uuid4(),uuid4(),[],[],job_id=uuid4(),run_created_at=datetime.now(timezone.utc))

    async def test_older_run_cannot_deactivate_newer_snapshot(self):
        from datetime import timedelta
        from module.structured_data.domain.models import Column, Dataset
        space,document = uuid4(),uuid4()
        dataset = Dataset(uuid4(),space,document,'a'*64,'source.xlsx','Sales','A1:B2','Sales',
            (Column('key','Key','string',1),),1,'structured/a.parquet','b'*64)
        now = datetime.now(timezone.utc)
        values = iter([True,None,now])
        statements = []
        class Session:
            async def execute(self,statement):
                statements.append(statement)
                value = next(values)
                return SimpleNamespace(scalar_one=lambda:value)
        await SqlDatasetCatalog(Session()).publish(space,document,[dataset],[[1.,0.]],job_id=uuid4(),
                                                   run_created_at=now-timedelta(days=1))
        self.assertEqual(len(statements),3)
        self.assertTrue(all(not str(statement).startswith('UPDATE') for statement in statements))

    async def test_publish_is_scoped_upsert_with_no_internal_commit(self):
        from sqlalchemy.dialects import postgresql
        from module.structured_data.domain.models import Column, Dataset
        space,document = uuid4(),uuid4()
        dataset = Dataset(uuid4(),space,document,'a'*64,'source.xlsx','Sales','A1:B2','Sales',
            (Column('key','Key','string',1),),1,'structured/a.parquet','b'*64)
        statements = []
        class Session:
            async def execute(self,statement):
                statements.append(statement)
                return SimpleNamespace(scalar_one=lambda:True if len(statements)==1 else None)
            async def commit(self):
                raise AssertionError('Extraction UOW owns the transaction')
        await SqlDatasetCatalog(Session()).publish(space,document,[dataset],[[1.,0.]],job_id=uuid4(),
                                                   run_created_at=datetime.now(timezone.utc))
        sql = str(statements[-1].compile(dialect=postgresql.dialect()))
        self.assertIn('ON CONFLICT',sql)
        self.assertIn('public.structured_datasets',sql)
        deactivate = str(statements[-2].compile(dialect=postgresql.dialect()))
        self.assertIn('knowledge_space_id',deactivate)
        self.assertIn('document_id',deactivate)
