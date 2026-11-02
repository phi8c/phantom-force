from contextlib import aclosing
import importlib.util
import unittest
from uuid import uuid4

from module.ingest.chunking.application.services.async_chunks import iterate_chunks
from module.ingest.chunking.domain.contracts.chunking_engine import Chunk


class AsyncChunkTests(unittest.IsolatedAsyncioTestCase):
    async def test_closing_stream_closes_source_iterator(self):
        stopped = []

        def source():
            try:
                yield Chunk(0, None, 'text', {})
                yield Chunk(1, None, 'text', {})
            finally:
                stopped.append(True)

        async with aclosing(iterate_chunks(source())) as stream:
            async for _ in stream:
                break
        self.assertEqual(stopped, [True])


@unittest.skipUnless(importlib.util.find_spec('sqlalchemy'), 'SQLAlchemy is not installed')
class ChunkPersistenceTests(unittest.IsolatedAsyncioTestCase):
    def make_writer(self, *, fail_write=False):
        from module.ingest.chunking.infrastructure.persistence.repositories.chunk_batch_writer_impl import ChunkBatchWriterImpl

        class Session:
            def __init__(self):
                self.added = []
                self.writes = []

            def add(self, value):
                self.added.append(value)

            async def flush(self):
                pass

            async def execute(self, statement, rows):
                if fail_write:
                    raise RuntimeError('Database write failed')
                self.writes.append(list(rows))

        class Writer(ChunkBatchWriterImpl):
            async def _lock_document_batches(self, document_id):
                pass

            async def get_by_job_and_document(self, **kwargs):
                return None

            async def _next_batch_index(self, document_id):
                return 0

        session = Session()
        return Writer(session, write_batch_size=3), session

    async def test_writer_consumes_incrementally_and_bulk_inserts(self):
        writer, session = self.make_writer()

        def chunks():
            for index in range(8):
                stored = sum(len(batch) for batch in session.writes)
                self.assertLessEqual(index - stored, 3)
                yield Chunk(index, None, f'Content {index}', {'source_block_ids': [f'b{index}']})

        result = await writer.create_with_chunks(ingestion_job_id=uuid4(), document_id=uuid4(), chunks=chunks())
        self.assertEqual(result.total_chunks, 8)
        self.assertEqual([len(batch) for batch in session.writes], [3, 3, 2])
        self.assertEqual(len(session.added), 1)
        self.assertEqual(session.writes[0][0]['metadata_payload']['source_block_ids'], ['b0'])

    async def test_empty_stream_is_rejected(self):
        writer, session = self.make_writer()
        with self.assertRaisesRegex(ValueError, 'zero chunks'):
            await writer.create_with_chunks(ingestion_job_id=uuid4(), document_id=uuid4(), chunks=iter(()))
        self.assertFalse(session.writes)

    async def test_failure_closes_source_without_committing_partial_batch(self):
        writer, _ = self.make_writer(fail_write=True)
        stopped = []

        def chunks():
            try:
                for index in range(5):
                    yield Chunk(index, None, 'Content', {})
            finally:
                stopped.append(True)

        with self.assertRaisesRegex(RuntimeError, 'Database write failed'):
            await writer.create_with_chunks(ingestion_job_id=uuid4(), document_id=uuid4(), chunks=chunks())
        self.assertEqual(stopped, [True])

    async def test_late_coverage_failure_propagates_to_transaction_owner(self):
        writer, session = self.make_writer()

        def chunks():
            for index in range(4):
                yield Chunk(index, None, 'Content', {})
            raise ValueError('Coverage missing at stream end')

        with self.assertRaisesRegex(ValueError, 'Coverage missing'):
            await writer.create_with_chunks(ingestion_job_id=uuid4(), document_id=uuid4(), chunks=chunks())
        self.assertEqual([len(batch) for batch in session.writes], [3])
