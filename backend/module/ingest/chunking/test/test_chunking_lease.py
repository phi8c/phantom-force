from datetime import datetime, timedelta, timezone
import importlib.util
import unittest
from uuid import uuid4


@unittest.skipUnless(importlib.util.find_spec('sqlalchemy'), 'SQLAlchemy not installed')
class ChunkingLeaseTests(unittest.IsolatedAsyncioTestCase):
    async def test_only_live_owner_renews_and_terminal_tasks_are_not_pending(self):
        from sqlalchemy import create_engine
        from module.ingest.chunking.infrastructure.persistence.repositories.chunking_task_repository_impl import ChunkingTaskRepositoryImpl
        engine = create_engine('sqlite://')
        try:
            with engine.connect() as connection:
                connection.exec_driver_sql('''CREATE TABLE chunking_tasks (
                    id TEXT PRIMARY KEY, ingestion_job_id TEXT, status TEXT,
                    claimed_by TEXT, lease_until DATETIME, updated_at DATETIME)''')

                class Session:
                    async def execute(self, statement):
                        return connection.execute(statement)

                repository = ChunkingTaskRepositoryImpl(Session())
                task, job = uuid4(), uuid4()
                now = datetime.now(timezone.utc)
                connection.exec_driver_sql('INSERT INTO chunking_tasks VALUES (?,?,?,?,?,?)',
                    (task.hex, job.hex, 'PROCESSING', 'owner',
                     (now + timedelta(minutes=5)).replace(tzinfo=None).isoformat(' '), now.isoformat(' ')))
                self.assertTrue(await repository.has_unfinished(job))
                self.assertFalse(await repository.renew_lease(task, claimed_by='other', lease_until=now + timedelta(minutes=10)))
                self.assertTrue(await repository.renew_lease(task, claimed_by='owner', lease_until=now + timedelta(minutes=10)))
                connection.exec_driver_sql("UPDATE chunking_tasks SET status='COMPLETED'")
                self.assertFalse(await repository.renew_lease(task, claimed_by='owner', lease_until=now + timedelta(minutes=10)))
                self.assertFalse(await repository.has_unfinished(job))
        finally:
            engine.dispose()
