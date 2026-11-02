from abc import ABC
from abc import abstractmethod
from typing import Any
from uuid import UUID

from module.ingest.knowledge.domain.entities import (
    KnowledgeDocumentType,
    KnowledgeDiscoveredRequestRecord,
    KnowledgeInformation,
    KnowledgeInformationField,
    KnowledgeInformationSearchRecord,
    KnowledgeInformationType,
    KnowledgeObject,
    KnowledgeObjectResolutionCandidate,
    KnowledgeRegistryEmbeddingTarget,
    KnowledgeRegistryEmbeddingUpdate,
    KnowledgeSemanticRequestVectors,
    KnowledgeTopic,
)


class KnowledgeRepository(ABC):

    @abstractmethod
    async def acquire_object_resolution_lock(
        self, *, knowledge_space_id: UUID, object_code: str
    ) -> None:
        pass

    @abstractmethod
    async def find_object_exact(
        self,
        *,
        knowledge_space_id: UUID,
        object_code: str,
        identifier_code: str | None,
    ) -> KnowledgeObject | None:
        pass

    @abstractmethod
    async def list_objects_by_type(
        self, *, knowledge_space_id: UUID, object_code: str
    ) -> list[KnowledgeObject]:
        pass

    @abstractmethod
    async def find_similar_objects(
        self,
        *,
        knowledge_space_id: UUID,
        object_code: str,
        object_embedding: list[float],
        identifier_embedding: list[float] | None,
        limit: int,
    ) -> list[KnowledgeObjectResolutionCandidate]:
        pass

    @abstractmethod
    async def add_verified_object_aliases(
        self, *, object_id: UUID, aliases: list[str]
    ) -> KnowledgeObject:
        pass

    @abstractmethod
    async def upsert_document_type(
        self,
        entity: KnowledgeDocumentType,
    ) -> KnowledgeDocumentType:
        pass

    @abstractmethod
    async def upsert_object(
        self,
        entity: KnowledgeObject,
    ) -> KnowledgeObject:
        pass

    @abstractmethod
    async def upsert_information_type(
        self,
        entity: KnowledgeInformationType,
    ) -> KnowledgeInformationType:
        pass

    @abstractmethod
    async def upsert_information_types(
        self,
        entities: list[KnowledgeInformationType],
    ) -> list[KnowledgeInformationType]:
        pass

    @abstractmethod
    async def upsert_information_field(
        self,
        entity: KnowledgeInformationField,
    ) -> KnowledgeInformationField:
        pass

    @abstractmethod
    async def upsert_information_fields(
        self,
        entities: list[KnowledgeInformationField],
    ) -> list[KnowledgeInformationField]:
        pass

    @abstractmethod
    async def upsert_topic(
        self,
        entity: KnowledgeTopic,
    ) -> KnowledgeTopic:
        pass

    @abstractmethod
    async def upsert_information(
        self,
        entity: KnowledgeInformation,
        source_identity: dict[str, Any],
    ) -> KnowledgeInformation:
        pass

    @abstractmethod
    async def list_missing_registry_embeddings(
        self,
        *,
        document_type_ids: list[UUID],
        information_type_ids: list[UUID],
        information_field_ids: list[UUID],
        object_ids: list[UUID],
        topic_ids: list[UUID],
    ) -> list[KnowledgeRegistryEmbeddingTarget]:
        pass

    @abstractmethod
    async def update_registry_embeddings(
        self,
        updates: list[KnowledgeRegistryEmbeddingUpdate],
    ) -> None:
        pass

    @abstractmethod
    async def search_information(
        self,
        *,
        knowledge_space_id: UUID,
        object_code: str,
        identifier_code: str | None,
        information_type_code: str | None,
        topic_codes: list[str],
    ) -> list[KnowledgeInformationSearchRecord]:
        pass

    @abstractmethod
    async def discover(
        self,
        *,
        knowledge_space_id: UUID,
        requests: list[dict[str, Any]],
        request_vectors: list[KnowledgeSemanticRequestVectors] | None = None,
    ) -> list[KnowledgeDiscoveredRequestRecord]:
        pass

    @abstractmethod
    async def retrieve_for_selection(
        self,
        *,
        knowledge_space_id: UUID,
        discovered_request: KnowledgeDiscoveredRequestRecord,
        information_type_codes: list[str],
        topic_codes: list[str],
        field_codes: list[str],
    ) -> list[KnowledgeInformationSearchRecord]:
        pass
