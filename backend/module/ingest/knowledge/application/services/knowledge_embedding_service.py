import logging
from collections.abc import Awaitable
from collections.abc import Callable
from uuid import UUID

from module.ingest.embedding.domain.contracts.text_embedding_provider import (
    TextEmbeddingProvider,
)
from module.ingest.knowledge.domain.contracts.knowledge_repository import (
    KnowledgeRepository,
)
from module.ingest.knowledge.domain.entities import (
    KnowledgeDocumentType,
    KnowledgeInformationField,
    KnowledgeInformationType,
    KnowledgeObject,
    KnowledgeRegistryEmbeddingUpdate,
    KnowledgeTopic,
)


logger = logging.getLogger(__name__)


class KnowledgeEmbeddingService:

    def __init__(
        self,
        repository: KnowledgeRepository,
        embedder_factory: Callable[
            [UUID],
            Awaitable[TextEmbeddingProvider],
        ],
    ):
        self._repository = repository
        self._embedder_factory = embedder_factory

    async def ensure_registry_embeddings(
        self,
        *,
        document_types: list[KnowledgeDocumentType],
        information_types: list[KnowledgeInformationType],
        information_fields: list[KnowledgeInformationField],
        objects: list[KnowledgeObject],
        topics: list[KnowledgeTopic],
    ) -> None:

        knowledge_space_id = self._knowledge_space_id(
            document_types=document_types,
            information_types=information_types,
            information_fields=information_fields,
            objects=objects,
            topics=topics,
        )
        if knowledge_space_id is None:
            return

        targets = await self._repository.list_missing_registry_embeddings(
            document_type_ids=[
                item.id
                for item in document_types
                if item.id is not None
            ],
            information_type_ids=[
                item.id
                for item in information_types
                if item.id is not None
            ],
            information_field_ids=[
                item.id
                for item in information_fields
                if item.id is not None
            ],
            object_ids=[
                item.id
                for item in objects
                if item.id is not None
            ],
            topic_ids=[
                item.id
                for item in topics
                if item.id is not None
            ],
        )
        if not targets:
            return

        unique_texts = list(
            dict.fromkeys(
                target.text
                for target in targets
                if target.text
            )
        )

        logger.info(
            "knowledge embedding batch input_count=%s unique_count=%s",
            len(targets),
            len(unique_texts),
        )

        embedder = await self._embedder_factory(knowledge_space_id)
        vectors = await embedder.embed_texts(unique_texts)
        vector_by_text = dict(
            zip(unique_texts, vectors, strict=True),
        )

        await self._repository.update_registry_embeddings(
            [
                KnowledgeRegistryEmbeddingUpdate(
                    kind=target.kind,
                    id=target.id,
                    embedding=vector_by_text[target.text],
                )
                for target in targets
            ],
        )

    @staticmethod
    def _knowledge_space_id(
        *,
        document_types: list[KnowledgeDocumentType],
        information_types: list[KnowledgeInformationType],
        information_fields: list[KnowledgeInformationField],
        objects: list[KnowledgeObject],
        topics: list[KnowledgeTopic],
    ) -> UUID | None:

        for collection in (
            document_types,
            information_types,
            information_fields,
            objects,
            topics,
        ):
            if collection:
                return collection[0].knowledge_space_id
        return None
