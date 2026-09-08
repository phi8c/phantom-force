from abc import ABC
from abc import abstractmethod
from typing import Any

from module.ingest.knowledge.domain.entities import (
    KnowledgeDocumentType,
    KnowledgeInformation,
    KnowledgeInformationField,
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
