from datetime import datetime, timezone
import unittest
from uuid import uuid4

from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session

from module.ingest.config.infrastructure.persistence.repositories.ingestion_config_repository_impl import IngestionConfigRepositoryImpl
from module.ingest.config.infrastructure.persistence.models.ingestion_job_model import IngestionJobModel
from module.ingest.config.domain.entities.ingestion_job_configuration import IngestionJobConfiguration
from module.ingest.master.composition.master_config_resolver import IngestionMasterConfigResolver


class ConfigurationQueryTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.engine = create_engine('sqlite://')
        self.statements = []
        event.listen(self.engine, 'before_cursor_execute',
                     lambda conn, cursor, statement, params, context, many: self.statements.append(statement))
        with self.engine.begin() as conn:
            conn.exec_driver_sql('''CREATE TABLE ingestion_jobs (
                id TEXT PRIMARY KEY, knowledge_space_id TEXT, trigger_type TEXT, status TEXT,
                is_build_graph BOOLEAN, total_files INTEGER, completed_files INTEGER, failed_files INTEGER,
                started_at DATETIME, finished_at DATETIME, created_at DATETIME, scope_type TEXT, scope_data JSON)''')
            conn.exec_driver_sql('''CREATE TABLE ingestion_job_configurations (
                id TEXT PRIMARY KEY, ingestion_job_id TEXT, is_classification BOOLEAN,
                model_set_id TEXT, chunking_strategy_id TEXT, extraction_engine_id TEXT, configuration JSON,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP, updated_at DATETIME DEFAULT CURRENT_TIMESTAMP)''')
            for table in ('extraction_engines', 'chunking_strategies', 'model_sets'):
                conn.exec_driver_sql(f'CREATE TABLE {table} (id TEXT PRIMARY KEY, code TEXT, enabled BOOLEAN)')
        self.session = Session(self.engine, expire_on_commit=False)
        sync = self.session
        class AsyncAdapter:
            async def execute(self, statement):
                return sync.execute(statement)
            def add(self, model):
                sync.add(model)
            async def flush(self):
                sync.flush()
        self.adapter = AsyncAdapter()
        self.repository = IngestionConfigRepositoryImpl(self.adapter)
        self.job_id = uuid4()
        self.session.add(IngestionJobModel(id=self.job_id, knowledge_space_id=uuid4(), trigger_type='MANUAL',
                                          created_at=datetime.now(timezone.utc)))
        self.session.flush()
        self.statements.clear()

    def tearDown(self):
        self.session.close()
        self.engine.dispose()

    def configuration(self, value):
        now = datetime.now(timezone.utc)
        return IngestionJobConfiguration(None, self.job_id, True, None, uuid4(), uuid4(), value, now, now)

    async def test_existing_configuration_write_is_one_statement_and_preserves_identity(self):
        original = await self.repository.save_configuration(self.configuration({'version': 1}))
        self.statements.clear()
        updated = await self.repository.save_configuration(self.configuration({'version': 2}))
        self.assertEqual(len(self.statements), 1)
        self.assertIn('RETURNING', self.statements[0])
        self.assertEqual(updated.id, original.id)
        # SQLite strips timezone information; PostgreSQL preserves it.
        self.assertEqual(updated.created_at.replace(tzinfo=None), original.created_at.replace(tzinfo=None))
        self.assertEqual(updated.configuration, {'version': 2})
        self.assertIsNotNone(updated.updated_at)

    async def test_new_configuration_needs_two_statements_without_refresh(self):
        value = await self.repository.save_configuration(self.configuration({'new': True}))
        self.assertEqual(len(self.statements), 2)
        self.assertIsNotNone(value.id)
        self.assertEqual(value.configuration, {'new': True})

    async def test_configuration_read_distinguishes_missing_job_from_unconfigured_job(self):
        self.assertIsNone(await self.repository.get_configuration_for_existing_job(self.job_id))
        self.assertEqual(len(self.statements), 1)
        self.statements.clear()
        with self.assertRaises(LookupError):
            await self.repository.get_configuration_for_existing_job(uuid4())
        self.assertEqual(len(self.statements), 1)

    async def test_configured_read_is_one_statement(self):
        saved = await self.repository.save_configuration(self.configuration({'value': 'original'}))
        self.statements.clear()
        loaded = await self.repository.get_configuration_for_existing_job(self.job_id)
        self.assertEqual(loaded.id, saved.id)
        self.assertEqual(loaded.configuration, {'value': 'original'})
        self.assertEqual(len(self.statements), 1)

    async def test_scope_update_returns_fresh_values_in_one_statement(self):
        job = await self.repository.update_job_scope(job_id=self.job_id, scope_type='ALL', scope_data={'path': '/'})
        self.assertEqual(job.scope_type, 'ALL')
        self.assertEqual(job.scope_data, {'path': '/'})
        self.assertEqual(len(self.statements), 1)
        with self.assertRaises(LookupError):
            await self.repository.update_job_scope(job_id=uuid4(), scope_type='ALL', scope_data={})

    async def test_master_resolution_is_one_query_and_validates_current_enabled_state(self):
        identities = [uuid4() for _ in range(3)]
        for table, code, identity in zip(('extraction_engines', 'chunking_strategies', 'model_sets'),
                                         ('Docling', 'Section', 'Default'), identities):
            self.session.connection().exec_driver_sql(f'INSERT INTO {table} VALUES (?,?,?)', (identity.hex, code, True))
        resolver = IngestionMasterConfigResolver(self.adapter)
        self.statements.clear()
        result = await resolver.resolve(extraction_engine_code=' docling ', chunking_strategy_code='section', model_set_code='default')
        self.assertEqual((result.extraction_engine_id, result.chunking_strategy_id, result.model_set_id), tuple(identities))
        self.assertEqual(len(self.statements), 1)
        self.session.connection().exec_driver_sql('UPDATE extraction_engines SET enabled=0')
        with self.assertRaisesRegex(ValueError, 'extraction_engine_code'):
            await resolver.resolve(extraction_engine_code='docling', chunking_strategy_code='section')

    async def test_optional_model_set_does_not_require_a_model_row(self):
        for table in ('extraction_engines', 'chunking_strategies'):
            self.session.connection().exec_driver_sql(f'INSERT INTO {table} VALUES (?,?,?)', (uuid4().hex, 'CODE', True))
        result = await IngestionMasterConfigResolver(self.adapter).resolve(extraction_engine_code='CODE', chunking_strategy_code='CODE')
        self.assertIsNone(result.model_set_id)

    async def test_missing_master_codes_keep_validation_errors(self):
        resolver = IngestionMasterConfigResolver(self.adapter)
        with self.assertRaisesRegex(ValueError, 'extraction_engine_code'):
            await resolver.resolve(extraction_engine_code='missing', chunking_strategy_code='missing')
        with self.assertRaisesRegex(ValueError, 'empty'):
            await resolver.resolve(extraction_engine_code=' ', chunking_strategy_code='missing')
