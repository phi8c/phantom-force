from datetime import datetime, timedelta, timezone
import importlib.util
import unittest
from uuid import uuid4


@unittest.skipUnless(importlib.util.find_spec('sqlalchemy'), 'SQLAlchemy not installed')
class ExtractionLeaseRepositoryTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        from sqlalchemy import create_engine
        from module.ingest.extraction.infrastructure.persistence.repositories.extraction_task_repository_impl import ExtractionTaskRepositoryImpl
        self.engine = create_engine('sqlite://')
        self.connection = self.engine.connect()
        self.connection.exec_driver_sql('''CREATE TABLE extraction_tasks (
            id TEXT PRIMARY KEY, ingestion_job_id TEXT, status TEXT,
            claimed_by TEXT, lease_until DATETIME, updated_at DATETIME)''')
        connection = self.connection

        class Session:
            async def execute(self, statement):
                return connection.execute(statement)

        self.repository = ExtractionTaskRepositoryImpl(Session())
        self.job_id = uuid4()

    def tearDown(self):
        self.connection.close()
        self.engine.dispose()

    def insert_task(self, *, owner='worker-a', status='PROCESSING', expired=False):
        task_id = uuid4()
        lease = datetime.now(timezone.utc) + timedelta(minutes=-5 if expired else 5)
        self.connection.exec_driver_sql(
            'INSERT INTO extraction_tasks VALUES (?, ?, ?, ?, ?, ?)',
            (task_id.hex, self.job_id.hex, status, owner,
             lease.replace(tzinfo=None).isoformat(' '), datetime.now().isoformat(' ')),
        )
        return task_id

    async def test_only_live_processing_owner_can_renew(self):
        fresh = self.insert_task()
        expired = self.insert_task(expired=True)
        completed = self.insert_task(status='COMPLETED')
        deadline = datetime.now(timezone.utc) + timedelta(minutes=10)
        self.assertFalse(await self.repository.renew_lease(fresh, claimed_by='other-worker', lease_until=deadline))
        self.assertFalse(await self.repository.renew_lease(expired, claimed_by='worker-a', lease_until=deadline))
        self.assertFalse(await self.repository.renew_lease(completed, claimed_by='worker-a', lease_until=deadline))
        self.assertTrue(await self.repository.renew_lease(fresh, claimed_by='worker-a', lease_until=deadline))

    async def test_unfinished_query_distinguishes_terminal_jobs(self):
        self.insert_task(status='COMPLETED')
        self.insert_task(status='FAILED')
        self.assertFalse(await self.repository.has_unfinished(self.job_id))
        self.insert_task(status='READY')
        self.assertTrue(await self.repository.has_unfinished(self.job_id))
        self.assertFalse(await self.repository.has_unfinished(uuid4()))
