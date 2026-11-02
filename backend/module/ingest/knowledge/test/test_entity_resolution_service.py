import asyncio
from copy import deepcopy
from uuid import UUID, uuid4

import pytest

from module.ingest.knowledge.application.services.entity_resolution_service import EntityResolutionService
from module.ingest.knowledge.domain.entities import KnowledgeObject, KnowledgeObjectResolutionCandidate


SPACE_ID = uuid4()


def entity(
    *,
    identifier_code: str,
    object_name: str,
    identifier_name: str | None = None,
    aliases=None,
    metadata=None,
) -> KnowledgeObject:
    return KnowledgeObject(
        id=None,
        knowledge_space_id=SPACE_ID,
        object_code="product",
        identifier_code=identifier_code,
        object_name=object_name,
        identifier_name=identifier_name,
        description=None,
        aliases=aliases,
        metadata=metadata,
        created_at=None,
        updated_at=None,
    )


@pytest.mark.asyncio
async def test_exact_match_does_not_call_embedding():
    repository = ResolutionRepository()
    canonical = await repository.upsert_object(entity(identifier_code="product_a", object_name="San pham A"))
    embedding = RecordingEmbeddingService()

    result = await EntityResolutionService(repository, embedding).resolve(
        entity(identifier_code="product_a", object_name="Product A")
    )

    assert result.id == canonical.id
    assert embedding.calls == 0


@pytest.mark.asyncio
async def test_verified_alias_match_does_not_call_embedding():
    repository = ResolutionRepository()
    canonical = await repository.upsert_object(
        entity(identifier_code="product_a", object_name="San pham A", aliases=["SP A"])
    )
    embedding = RecordingEmbeddingService()

    result = await EntityResolutionService(repository, embedding).resolve(
        entity(identifier_code="sp_a", object_name="SP A")
    )

    assert result.id == canonical.id
    assert embedding.calls == 0


@pytest.mark.asyncio
async def test_synonymous_name_reuses_canonical_object_and_adds_alias():
    repository = ResolutionRepository(distance=0.08)
    canonical = await repository.upsert_object(
        entity(identifier_code="product_a", object_name="San pham A")
    )

    result = await EntityResolutionService(repository, RecordingEmbeddingService()).resolve(
        entity(identifier_code="sp_a", object_name="SP A")
    )

    assert result.id == canonical.id
    assert "SP A" in result.aliases
    assert "sp_a" in result.aliases
    assert len(repository.objects) == 1


@pytest.mark.asyncio
async def test_semantically_close_but_conflicting_entity_is_not_merged():
    repository = ResolutionRepository(distance=0.03)
    canonical = await repository.upsert_object(
        entity(
            identifier_code="product_a",
            object_name="Premium savings account",
            metadata={"country": "VN"},
        )
    )

    result = await EntityResolutionService(repository, RecordingEmbeddingService()).resolve(
        entity(
            identifier_code="product_b",
            object_name="Premium savings plan",
            metadata={"country": "US"},
        )
    )

    assert result.id != canonical.id
    assert result.metadata["entity_resolution"]["status"] == "review_required"


@pytest.mark.asyncio
async def test_ambiguous_candidates_are_recorded_for_review():
    repository = ResolutionRepository(distance=0.05)
    first = await repository.upsert_object(entity(identifier_code="product_a", object_name="San pham A"))
    second = await repository.upsert_object(entity(identifier_code="legacy_a", object_name="San pham A"))

    result = await EntityResolutionService(repository, RecordingEmbeddingService()).resolve(
        entity(identifier_code="sp_a", object_name="SP A")
    )

    assert result.id not in {first.id, second.id}
    assert set(result.metadata["entity_resolution"]["candidate_ids"]) == {str(first.id), str(second.id)}


@pytest.mark.asyncio
async def test_concurrent_ingestion_produces_one_canonical_object():
    repository = ResolutionRepository(distance=0.05)
    service = EntityResolutionService(repository, RecordingEmbeddingService())

    first, second = await asyncio.gather(
        service.resolve(entity(identifier_code="product_a", object_name="San pham A")),
        service.resolve(entity(identifier_code="sp_a", object_name="SP A")),
    )

    assert first.id == second.id
    assert len(repository.objects) == 1


class RecordingEmbeddingService:
    def __init__(self):
        self.calls = 0

    async def embed_object(self, _entity):
        self.calls += 1
        return [1.0, 0.0], [1.0, 0.0]

    async def ensure_registry_embeddings(self, **_kwargs):
        return None


class ResolutionRepository:
    def __init__(self, *, distance: float = 0.1):
        self.objects: list[KnowledgeObject] = []
        self.distance = distance
        self._lock = asyncio.Lock()

    async def acquire_object_resolution_lock(self, **_kwargs):
        await self._lock.acquire()

    def _release_lock(self):
        if self._lock.locked():
            self._lock.release()

    async def find_object_exact(self, *, knowledge_space_id, object_code, identifier_code):
        return next(
            (
                item for item in self.objects
                if item.knowledge_space_id == knowledge_space_id
                and item.object_code == object_code
                and item.identifier_code == identifier_code
            ),
            None,
        )

    async def list_objects_by_type(self, *, knowledge_space_id, object_code):
        return [
            item for item in self.objects
            if item.knowledge_space_id == knowledge_space_id and item.object_code == object_code
        ]

    async def find_similar_objects(self, *, knowledge_space_id, object_code, **_kwargs):
        return [
            KnowledgeObjectResolutionCandidate(item, self.distance)
            for item in await self.list_objects_by_type(
                knowledge_space_id=knowledge_space_id,
                object_code=object_code,
            )
        ]

    async def add_verified_object_aliases(self, *, object_id: UUID, aliases: list[str]):
        item = next(item for item in self.objects if item.id == object_id)
        item.aliases = list(item.aliases or [])
        for alias in aliases:
            if alias not in item.aliases:
                item.aliases.append(alias)
        self._release_lock()
        return item

    async def upsert_object(self, item):
        existing = await self.find_object_exact(
            knowledge_space_id=item.knowledge_space_id,
            object_code=item.object_code,
            identifier_code=item.identifier_code,
        )
        if existing is not None:
            self._release_lock()
            return existing
        stored = deepcopy(item)
        stored.id = uuid4()
        self.objects.append(stored)
        self._release_lock()
        return stored
