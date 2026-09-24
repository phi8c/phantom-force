from __future__ import annotations

import unittest
from types import SimpleNamespace
from uuid import uuid4

from sqlalchemy.dialects import postgresql

from module.knowledge_space.infrastructure.persistence.repositories.knowledge_space_queue_repository_impl import (
    KnowledgeSpaceQueueRepositoryImpl,
)


class FakeResult:
    def __init__(self, row) -> None:
        self._row = row

    def one_or_none(self):
        return self._row


class FakeSession:
    def __init__(self, row=None) -> None:
        self.row = row
        self.statement = None

    async def execute(self, statement):
        self.statement = statement
        return FakeResult(self.row)


def model(**values):
    defaults = {
        "id": uuid4(),
        "knowledge_space_id": uuid4(),
        "queue_provider_id": uuid4(),
        "configuration": {},
        "is_default": True,
        "enabled": True,
        "code": "rabbitmq",
        "name": "RabbitMQ",
        "description": None,
        "created_at": None,
        "updated_at": None,
    }
    defaults.update(values)
    return SimpleNamespace(**defaults)


class KnowledgeSpaceQueueRepositoryTests(unittest.IsolatedAsyncioTestCase):
    async def test_maps_default_queue_and_provider(self) -> None:
        mapping = model(configuration={"not_used": True})
        provider = model(
            id=mapping.queue_provider_id,
            code="rabbitmq",
        )
        session = FakeSession((mapping, provider))
        repository = KnowledgeSpaceQueueRepositoryImpl(session)
        knowledge_space_id = uuid4()

        result = await repository.get_default_for_knowledge_space(
            knowledge_space_id
        )

        self.assertEqual(result.provider.code, "rabbitmq")
        self.assertEqual(result.configuration, {"not_used": True})
        compiled = str(
            session.statement.compile(
                dialect=postgresql.dialect(),
                compile_kwargs={"literal_binds": False},
            )
        )
        self.assertIn("knowledge_space_queues", compiled)
        self.assertIn("queue_providers", compiled)
        self.assertIn("knowledge_space_queues.is_default IS true", compiled)

    async def test_returns_none_when_no_default_mapping_exists(self) -> None:
        repository = KnowledgeSpaceQueueRepositoryImpl(FakeSession())

        result = await repository.get_default_for_knowledge_space(uuid4())

        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
