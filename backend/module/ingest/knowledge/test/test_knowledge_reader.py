from uuid import uuid4

import pytest

from module.ingest.knowledge.application.dtos import (
    KnowledgeDiscoveryRequest,
    KnowledgeDiscoveryRequestItem,
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
            items=[
                KnowledgeDiscoveryRequestItem(
                    request_id="knowledge_1",
                    need="Find AI housing trends",
                    object_seeds=[
                        "artificial_intelligence",
                    ],
                    information_type_seeds=[
                        "trend",
                    ],
                    topic_seeds=[
                        "housing_market_trends",
                    ],
                ),
                KnowledgeDiscoveryRequestItem(
                    request_id="knowledge_2",
                    need="Find Gen Z AI housing trends",
                    object_seeds=[
                        "artificial_intelligence",
                    ],
                    identifier_seeds=[
                        "gen_z",
                    ],
                    information_type_seeds=[
                        "trend",
                    ],
                    topic_seeds=[
                        "housing_market_trends",
                    ],
                ),
            ],
        )
    )

    assert embedder.calls == [
        [
            "housing_market_trends",
            "artificial_intelligence",
            "trend",
            "gen_z",
        ]
    ]
    assert repository.calls[0]["knowledge_space_id"] == knowledge_space_id
    request_vectors = repository.calls[0]["request_vectors"]
    assert len(request_vectors) == 2
    assert request_vectors[0].object_vectors == {
        "artificial_intelligence": [2.0],
    }
    assert request_vectors[1].identifier_vectors == {
        "gen_z": [4.0],
    }


@pytest.mark.asyncio
async def test_discovery_embeds_grouped_request_seed_lists_without_permutation():
    repository = RecordingDiscoveryRepository()
    embedder = FakeTextEmbeddingProvider()
    reader = KnowledgeReader(
        repository=repository,
        embedder_factory=lambda knowledge_space_id: fake_embedder(
            embedder,
        ),
    )

    await reader.discover(
        KnowledgeDiscoveryRequest(
            knowledge_space_id=uuid4(),
            items=[
                KnowledgeDiscoveryRequestItem(
                    request_id="knowledge_1",
                    need="Compare cache policy",
                    document_type_seeds=[
                        "technical_document",
                    ],
                    head_seeds=[
                        "browser_policy",
                    ],
                    topic_seeds=[
                        "cache_policy",
                        "browser_cache",
                    ],
                    object_seeds=[
                        "chrome",
                        "edge",
                    ],
                    identifier_seeds=[
                        "chrome",
                    ],
                    information_type_seeds=[
                        "policy",
                        "configuration",
                    ],
                    information_field_seeds=[
                        "ttl",
                    ],
                    constraints={
                        "scope": "comparison",
                    },
                )
            ],
        )
    )

    assert embedder.calls == [
        [
            "technical_document",
            "cache_policy",
            "browser_cache",
            "chrome",
            "edge",
            "policy",
            "configuration",
            "ttl",
        ]
    ]
    call = repository.calls[0]
    assert len(call["requests"]) == 1
    assert call["requests"][0]["request_id"] == "knowledge_1"
    assert call["requests"][0]["need"] == "Compare cache policy"
    assert call["requests"][0]["head_seeds"] == [
        "browser_policy",
    ]
    vectors = call["request_vectors"][0]
    assert vectors.document_type_vectors == {
        "technical_document": [1.0],
    }
    assert vectors.topic_vectors == {
        "cache_policy": [2.0],
        "browser_cache": [3.0],
    }
    assert vectors.object_vectors == {
        "chrome": [4.0],
        "edge": [5.0],
    }
    assert vectors.identifier_vectors == {
        "chrome": [4.0],
    }
    assert vectors.information_type_vectors == {
        "policy": [6.0],
        "configuration": [7.0],
    }
    assert vectors.information_field_vectors == {
        "ttl": [8.0],
    }


@pytest.mark.asyncio
async def test_discovery_preserves_one_request_and_skips_head_embedding():
    repository = RecordingDiscoveryRepository()
    embedder = FakeTextEmbeddingProvider()
    reader = KnowledgeReader(
        repository=repository,
        embedder_factory=lambda knowledge_space_id: fake_embedder(
            embedder,
        ),
    )

    await reader.discover(
        KnowledgeDiscoveryRequest(
            knowledge_space_id=uuid4(),
            items=[
                KnowledgeDiscoveryRequestItem(
                    request_id="knowledge_1",
                    need="Find requirements across topics",
                    head_seeds=[
                        "acceptance section",
                    ],
                    topic_seeds=[
                        "acceptance",
                        "deployment",
                        "acceptance",
                    ],
                    object_seeds=[
                        "project",
                    ],
                )
            ],
        )
    )

    assert embedder.calls == [
        [
            "acceptance",
            "deployment",
            "project",
        ]
    ]
    call = repository.calls[0]
    assert len(call["requests"]) == 1
    assert call["requests"][0]["request_id"] == "knowledge_1"
    assert call["requests"][0]["head_seeds"] == [
        "acceptance section",
    ]
    vectors = call["request_vectors"][0]
    assert vectors.request_id == "knowledge_1"
    assert vectors.topic_vectors == {
        "acceptance": [1.0],
        "deployment": [2.0],
    }
    assert vectors.object_vectors == {
        "project": [3.0],
    }


class RecordingDiscoveryRepository:
    def __init__(self):
        self.calls = []

    async def discover(
        self,
        *,
        knowledge_space_id,
        requests,
        request_vectors=None,
    ):
        self.calls.append(
            {
                "knowledge_space_id": knowledge_space_id,
                "requests": requests,
                "request_vectors": request_vectors,
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
