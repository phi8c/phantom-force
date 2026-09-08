from abc import ABC
from abc import abstractmethod
from typing import Any
from uuid import UUID

from module.ingest.knowledge.domain.entities import (
    KnowledgeDocumentType,
    KnowledgeInformation,
    KnowledgeInformationField,
    KnowledgeInformationSearchRecord,
    KnowledgeInformationType,
    KnowledgeObject,
    KnowledgeTopic,
)


class KnowledgeRepository(ABC):

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
    async def upsert_information_field(
        self,
        entity: KnowledgeInformationField,
    ) -> KnowledgeInformationField:
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
