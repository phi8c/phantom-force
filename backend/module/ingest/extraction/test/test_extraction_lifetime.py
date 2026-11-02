import asyncio
import json
from pathlib import Path
import tempfile
import unittest

from module.ingest.extraction.application.services.extraction_output_stream import extraction_output_stream
from module.ingest.extraction.domain.contracts.extraction_engine import ExtractionResult
from workers.ingest.task_lease import execute_with_lease


class ExtractionLifetimeTests(unittest.IsolatedAsyncioTestCase):
    async def test_heartbeat_runs_while_operation_waits(self):
        finished = asyncio.Event()
        renewals = []

        async def operation():
            await finished.wait()
            return 'done'

        async def renew():
            renewals.append(True)
            finished.set()
            return True

        async def completed():
            return False

        result = await asyncio.wait_for(execute_with_lease(operation(), renew=renew, completed=completed, interval=0.01), 1)
        self.assertEqual(result, 'done')
        self.assertTrue(renewals)

    async def test_lease_loss_cancels_and_awaits_operation(self):
        stopped = asyncio.Event()

        async def operation():
            try:
                await asyncio.Event().wait()
            finally:
                stopped.set()

        async def no():
            return False

        with self.assertRaisesRegex(RuntimeError, 'lease was lost'):
            await execute_with_lease(operation(), renew=no, completed=no, interval=0.01)
        self.assertTrue(stopped.is_set())

    async def test_completed_task_can_finish_dispatch_after_releasing_lease(self):
        finish_dispatch = asyncio.Event()

        async def operation():
            await finish_dispatch.wait()
            return 'dispatched'

        async def renew():
            return False

        async def completed():
            finish_dispatch.set()
            return True

        result = await execute_with_lease(operation(), renew=renew, completed=completed, interval=0.01)
        self.assertEqual(result, 'dispatched')

    async def test_disk_stream_replaces_uuid_without_materializing_arrays(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'assembled.json'
            payload = 'Dữ liệu ' * 20000
            path.write_text('{"document_id":"old",\n"blocks":' + json.dumps([payload], ensure_ascii=False) + '}', encoding='utf-8')
            result = ExtractionResult(content={'document_id': 'actual-uuid'}, content_file=path)
            chunks = [block async for block in extraction_output_stream(result)]
            self.assertGreater(len(chunks), 2)
            self.assertTrue(all(len(block) <= 64 * 1024 for block in chunks[1:]))
            decoded = json.loads(b''.join(chunks))
            self.assertEqual(decoded['document_id'], 'actual-uuid')
            self.assertEqual(decoded['blocks'], [payload])

    async def test_legacy_in_memory_stream_remains_valid(self):
        result = ExtractionResult(content={'sections': [{'content': 'text'}]})
        content = b''.join([block async for block in extraction_output_stream(result)])
        self.assertEqual(json.loads(content), result.content)
