import logging
from copy import deepcopy

from module.ingest.knowledge.application.services.knowledge_embedding_service import (
    KnowledgeEmbeddingService,
)
from module.ingest.knowledge.domain.contracts.knowledge_repository import (
    KnowledgeRepository,
)
from module.ingest.knowledge.domain.entities import KnowledgeObject
from module.ingest.knowledge.domain.object_semantics import normalize_entity_text


logger = logging.getLogger(__name__)


class EntityResolutionService:
    _TOP_K = 5
    _MAX_DISTANCE = 0.25

    def __init__(
        self,
        repository: KnowledgeRepository,
        embedding_service: KnowledgeEmbeddingService,
    ):
        self._repository = repository
        self._embedding_service = embedding_service

    async def resolve(self, entity: KnowledgeObject) -> KnowledgeObject:
        await self._repository.acquire_object_resolution_lock(
            knowledge_space_id=entity.knowledge_space_id,
            object_code=entity.object_code,
        )
        exact = await self._repository.find_object_exact(
            knowledge_space_id=entity.knowledge_space_id,
            object_code=entity.object_code,
            identifier_code=entity.identifier_code,
        )
        if exact is not None:
            return await self._repository.upsert_object(entity)

        same_type = await self._repository.list_objects_by_type(
            knowledge_space_id=entity.knowledge_space_id,
            object_code=entity.object_code,
        )
        alias_match = self._alias_match(entity, same_type)
        if alias_match is not None:
            return await self._merge(alias_match, entity)

        await self._embedding_service.ensure_registry_embeddings(
            document_types=[],
            information_types=[],
            information_fields=[],
            objects=same_type,
            topics=[],
        )
        object_vector, identifier_vector = await self._embedding_service.embed_object(
            entity,
        )
        candidates = await self._repository.find_similar_objects(
            knowledge_space_id=entity.knowledge_space_id,
            object_code=entity.object_code,
            object_embedding=object_vector,
            identifier_embedding=identifier_vector,
            limit=self._TOP_K,
        )
        plausible = [
            item.object
            for item in candidates
            if item.distance <= self._MAX_DISTANCE
            and self._has_identity_evidence(entity, item.object)
            and not self._has_conflict(entity, item.object)
        ]
        if len(plausible) == 1:
            return await self._merge(plausible[0], entity)

        if candidates:
            entity = self._mark_for_review(entity, [item.object for item in candidates])
            logger.warning(
                "knowledge entity_resolution_review_required space=%s object_code=%s identifier=%s candidates=%s",
                entity.knowledge_space_id,
                entity.object_code,
                entity.identifier_code,
                [str(item.object.id) for item in candidates],
            )
        return await self._repository.upsert_object(entity)

    async def _merge(
        self,
        canonical: KnowledgeObject,
        incoming: KnowledgeObject,
    ) -> KnowledgeObject:
        aliases = [
            value
            for value in (
                incoming.object_name,
                incoming.identifier_name,
                incoming.identifier_code,
            )
            if value and normalize_entity_text(value) not in self._identity_values(canonical)
        ]
        if not aliases:
            return canonical
        return await self._repository.add_verified_object_aliases(
            object_id=canonical.id,
            aliases=aliases,
        )

    @classmethod
    def _alias_match(
        cls,
        incoming: KnowledgeObject,
        objects: list[KnowledgeObject],
    ) -> KnowledgeObject | None:
        incoming_values = cls._identity_values(incoming)
        matches = [
            item
            for item in objects
            if incoming_values & cls._verified_aliases(item.aliases)
        ]
        return matches[0] if len(matches) == 1 else None

    @classmethod
    def _has_identity_evidence(
        cls,
        left: KnowledgeObject,
        right: KnowledgeObject,
    ) -> bool:
        if left.identifier_code and right.identifier_code:
            if normalize_entity_text(left.identifier_code) == normalize_entity_text(
                right.identifier_code,
            ):
                return True
        for left_value in cls._identity_values(left):
            for right_value in cls._identity_values(right):
                if cls._meaningful_equivalent(left_value, right_value):
                    return True
        return False

    @staticmethod
    def _meaningful_equivalent(left: str, right: str) -> bool:
        if left == right and len(left) >= 3:
            return True
        left_tokens, right_tokens = left.split(), right.split()
        for short, long in ((left_tokens, right_tokens), (right_tokens, left_tokens)):
            if len(short) < 2 or len(long) < 2:
                continue
            if len(short[0]) < 2 or len(long[0]) <= len(short[0]):
                continue
            acronym = "".join(token[0] for token in long[: len(short[0])])
            if short[0] == acronym and short[1:] == long[len(short[0]):]:
                return True
        return False

    @staticmethod
    def _has_conflict(left: KnowledgeObject, right: KnowledgeObject) -> bool:
        if left.identifier_code and right.identifier_code:
            identifiers_differ = normalize_entity_text(
                left.identifier_code,
            ) != normalize_entity_text(right.identifier_code)
            names_support_identity = any(
                EntityResolutionService._meaningful_equivalent(left_name, right_name)
                for left_name in EntityResolutionService._name_values(left)
                for right_name in EntityResolutionService._name_values(right)
            )
            if identifiers_differ and not names_support_identity:
                return True
        left_metadata, right_metadata = left.metadata or {}, right.metadata or {}
        ignored = {"entity_resolution", "embedding_text_versions"}
        return any(
            key not in ignored and left_metadata[key] is not None and right_metadata[key] is not None
            and left_metadata[key] != right_metadata[key]
            for key in left_metadata.keys() & right_metadata.keys()
        )

    @classmethod
    def _identity_values(cls, entity: KnowledgeObject) -> set[str]:
        return {
            normalized for value in (entity.object_name, entity.identifier_name, entity.identifier_code)
            if (normalized := normalize_entity_text(value))
        }

    @staticmethod
    def _name_values(entity: KnowledgeObject) -> set[str]:
        return {
            normalized for value in (entity.object_name, entity.identifier_name)
            if (normalized := normalize_entity_text(value))
        }

    @staticmethod
    def _verified_aliases(aliases) -> set[str]:
        values = []
        if isinstance(aliases, list):
            values = [item for item in aliases if isinstance(item, str)]
            values += [
                item.get("value")
                for item in aliases
                if isinstance(item, dict) and item.get("verified") is True
            ]
        elif isinstance(aliases, dict):
            values = aliases.get("verified", []) if isinstance(aliases.get("verified"), list) else []
        return {normalize_entity_text(value) for value in values if value}

    @staticmethod
    def _mark_for_review(entity: KnowledgeObject, candidates: list[KnowledgeObject]) -> KnowledgeObject:
        marked = deepcopy(entity)
        marked.metadata = deepcopy(entity.metadata or {})
        marked.metadata["entity_resolution"] = {
            "status": "review_required",
            "candidate_ids": [
                str(item.id)
                for item in candidates
                if item.id is not None
            ],
        }
        return marked
