from uuid import uuid4

import pytest

from module.ingest.knowledge.application.dtos import (
    KnowledgeDiscoveryRequest,
    KnowledgeDiscoverySeed,
)
from module.ingest.knowledge.application.services.knowledge_reader import (
    KnowledgeReader,
)


@pytest.mark.asyncio
async def test_discovery_embeds_seed_strings_in_one_deduplicated_batch():
    repository = RecordingDiscoveryRepository()
    embedder = FakeTextEmbeddingProvider()
    reader = KnowledgeReader(
        repository=repository,
        embedder_factory=lambda knowledge_space_id: fake_embedder(
            embedder,
        ),
    )
    knowledge_space_id = uuid4()

    await reader.discover(
        KnowledgeDiscoveryRequest(
            knowledge_space_id=knowledge_space_id,
            seeds=[
                KnowledgeDiscoverySeed(
                    seed_id="seed-1",
                    object_code="artificial_intelligence",
                    information_type_code="trend",
                    topic_codes=[
                        "housing_market_trends",
                    ],
                ),
                KnowledgeDiscoverySeed(
                    seed_id="seed-2",
                    object_code="artificial_intelligence",
                    identifier_code="gen_z",
                    information_type_code="trend",
                    topic_codes=[
                        "housing_market_trends",
                    ],
                ),
            ],
        )
    )

    assert embedder.calls == [
        [
            "artificial_intelligence",
            "trend",
            "housing_market_trends",
            "gen_z",
        ]
    ]
    assert repository.calls[0]["knowledge_space_id"] == knowledge_space_id
    seed_vectors = repository.calls[0]["seed_vectors"]
    assert len(seed_vectors) == 2
    assert seed_vectors[0].object_vector == [1.0]
    assert seed_vectors[1].identifier_vector == [4.0]


class RecordingDiscoveryRepository:
    def __init__(self):
        self.calls = []

    async def discover(
        self,
        *,
        knowledge_space_id,
        seeds,
        seed_vectors=None,
    ):
        self.calls.append(
            {
                "knowledge_space_id": knowledge_space_id,
                "seeds": seeds,
                "seed_vectors": seed_vectors,
            }
        )
        return []


class FakeTextEmbeddingProvider:
    def __init__(self):
        self.calls = []

    async def embed_texts(self, texts):
        self.calls.append(list(texts))
        return [
            [float(index + 1)]
            for index, _ in enumerate(texts)
        ]


async def fake_embedder(embedder):
    return embedder
