from typing import Any

from module.ingest.knowledge.application.dtos.knowledge_write_request import (
    KnowledgeWriteRequest,
)
from module.ingest.knowledge.domain.contracts.knowledge_repository import (
    KnowledgeRepository,
)
from module.ingest.knowledge.domain.entities import (
    KnowledgeDocumentType,
    KnowledgeInformation,
    KnowledgeInformationField,
    KnowledgeInformationType,
    KnowledgeObject,
    KnowledgeTopic,
)
from module.ingest.knowledge.domain.enums import (
    KnowledgeFieldDataType,
)


class KnowledgeWriter:

    def __init__(
        self,
        repository: KnowledgeRepository,
    ):
        self._repository = repository

    async def write(
        self,
        request: KnowledgeWriteRequest,
    ) -> None:

        raw_response = dict(request.raw_response or {})
        structured_response = self._structured_payload(
            raw_response,
        )
        knowledge_space_id = await (
            self._repository.get_knowledge_space_id_by_job_id(
                request.ingestion_job_id,
            )
        )

        if knowledge_space_id is None:
            raise ValueError(
                "Knowledge space not found for ingestion job",
            )

        document_types = await self._upsert_document_types(
            knowledge_space_id,
            structured_response,
        )
        information_types = await self._upsert_information_types(
            knowledge_space_id,
            structured_response,
        )
        await self._upsert_information_fields(
            knowledge_space_id,
            structured_response,
        )
        objects = await self._upsert_objects(
            knowledge_space_id,
            structured_response,
        )
        topics = await self._upsert_topics(
            knowledge_space_id,
            structured_response,
        )

        for item in self._items(
            structured_response,
            "information",
            "knowledge_information",
            "knowledge",
        ):
            summary = item.get("summary")
            if not summary:
                continue

            information_type_id = None
            information_type_code = item.get(
                "information_type_code",
            ) or item.get("type_code")
            if information_type_code:
                information_type = information_types.get(
                    str(information_type_code),
                )
                if information_type is not None:
                    information_type_id = information_type.id

            source_confidence = self._confidence(
                item.get("confidence"),
            )

            await self._repository.add_information(
                KnowledgeInformation(
                    id=None,
                    knowledge_space_id=knowledge_space_id,
                    information_type_id=information_type_id,
                    summary=str(summary),
                    data=item.get("data"),
                    object_refs=self._object_refs(
                        item,
                        objects,
                    ),
                    topic_refs=self._topic_refs(
                        item,
                        topics,
                    ),
                    source_refs=[
                        {
                            "document_id": str(
                                request.document_id,
                            ),
                            "chunk_id": str(
                                request.chunk_id,
                            ),
                            "confidence": source_confidence,
                        }
                    ],
                    confidence=source_confidence,
                    raw_model_output=raw_response,
                    metadata={
                        "model_name": request.model_name,
                        "document_types": [
                            document_type.code
                            for document_type
                            in document_types.values()
                        ],
                    },
                    created_at=None,
                    updated_at=None,
                )
            )

    async def _upsert_document_types(
        self,
        knowledge_space_id,
        raw_response: dict[str, Any],
    ):

        result = {}
        for item in self._items(
            raw_response,
            "document_types",
            "document_type",
        ):
            code = item.get("code")
            if not code:
                continue
            entity = await self._repository.upsert_document_type(
                KnowledgeDocumentType(
                    id=None,
                    knowledge_space_id=knowledge_space_id,
                    code=str(code),
                    name=item.get("name"),
                    description=item.get("description"),
                    structuring_guidance=item.get(
                        "structuring_guidance",
                    ),
                    metadata=item.get("metadata"),
                    created_at=None,
                    updated_at=None,
                )
            )
            result[entity.code] = entity
        return result

    async def _upsert_information_types(
        self,
        knowledge_space_id,
        raw_response: dict[str, Any],
    ):

        result = {}
        for item in self._items(
            raw_response,
            "information_types",
            "information_type",
        ):
            code = item.get("code")
            if not code:
                continue
            entity = await self._repository.upsert_information_type(
                KnowledgeInformationType(
                    id=None,
                    knowledge_space_id=knowledge_space_id,
                    code=str(code),
                    name=item.get("name"),
                    description=item.get("description"),
                    metadata=item.get("metadata"),
                    created_at=None,
                    updated_at=None,
                )
            )
            result[entity.code] = entity
        return result

    async def _upsert_information_fields(
        self,
        knowledge_space_id,
        raw_response: dict[str, Any],
    ) -> None:

        for item in self._items(
            raw_response,
            "information_fields",
            "fields",
        ):
            code = item.get("code")
            if not code:
                continue
            await self._repository.upsert_information_field(
                KnowledgeInformationField(
                    id=None,
                    knowledge_space_id=knowledge_space_id,
                    code=str(code),
                    name=item.get("name"),
                    description=item.get("description"),
                    data_type=self._data_type(
                        item.get("data_type"),
                    ),
                    unit_type=item.get("unit_type"),
                    metadata=item.get("metadata"),
                    created_at=None,
                    updated_at=None,
                )
            )

    async def _upsert_objects(
        self,
        knowledge_space_id,
        raw_response: dict[str, Any],
    ):

        result = {}
        for item in self._items(raw_response, "objects"):
            object_code = item.get("object_code") or item.get("code")
            if not object_code:
                continue
            entity = await self._repository.upsert_object(
                KnowledgeObject(
                    id=None,
                    knowledge_space_id=knowledge_space_id,
                    object_code=str(object_code),
                    identifier_code=self._optional_str(
                        item.get("identifier_code"),
                    ),
                    object_name=item.get("object_name")
                    or item.get("name"),
                    identifier_name=item.get(
                        "identifier_name",
                    ),
                    description=item.get("description"),
                    aliases=item.get("aliases"),
                    metadata=item.get("metadata"),
                    created_at=None,
                    updated_at=None,
                )
            )
            result[
                self._object_key(
                    entity.object_code,
                    entity.identifier_code,
                )
            ] = entity
        return result

    async def _upsert_topics(
        self,
        knowledge_space_id,
        raw_response: dict[str, Any],
    ):

        result = {}
        for item in self._items(raw_response, "topics"):
            code = item.get("code")
            if not code:
                continue
            entity = await self._repository.upsert_topic(
                KnowledgeTopic(
                    id=None,
                    knowledge_space_id=knowledge_space_id,
                    code=str(code),
                    name=item.get("name"),
                    description=item.get("description"),
                    metadata=item.get("metadata"),
                    created_at=None,
                    updated_at=None,
                )
            )
            result[entity.code] = entity
        return result

    @staticmethod
    def _items(
        raw_response: dict[str, Any],
        *keys: str,
    ) -> list[dict[str, Any]]:

        for key in keys:
            value = raw_response.get(key)
            if isinstance(value, list):
                return [
                    item
                    for item in value
                    if isinstance(item, dict)
                ]
            if isinstance(value, dict):
                return [value]
        return []

    @staticmethod
    def _structured_payload(
        raw_response: dict[str, Any],
    ) -> dict[str, Any]:

        structured = raw_response.get(
            "structured_knowledge",
        )
        if isinstance(
            structured,
            dict,
        ):
            return structured

        knowledge = raw_response.get(
            "knowledge",
        )
        if isinstance(
            knowledge,
            dict,
        ):
            return knowledge

        return raw_response

    @classmethod
    def _object_refs(
        cls,
        item: dict[str, Any],
        objects,
    ) -> list[dict[str, Any]] | None:

        refs = []
        for ref in cls._items(item, "object_refs", "objects"):
            object_code = ref.get("object_code") or ref.get("code")
            if not object_code:
                continue
            object_ref = objects.get(
                cls._object_key(
                    str(object_code),
                    cls._optional_str(
                        ref.get("identifier_code"),
                    ),
                )
            )
            if object_ref is None:
                continue
            refs.append(
                {
                    "object_id": str(object_ref.id),
                    "object_code": object_ref.object_code,
                    "identifier_code": (
                        object_ref.identifier_code
                    ),
                }
            )
        return refs or None

    @staticmethod
    def _topic_refs(
        item: dict[str, Any],
        topics,
    ) -> list[dict[str, Any]] | None:

        refs = []
        topic_values = item.get("topic_refs") or item.get("topics") or []
        for ref in topic_values:
            code = ref.get("code") if isinstance(ref, dict) else ref
            if not code:
                continue
            topic = topics.get(str(code))
            if topic is None:
                continue
            refs.append(
                {
                    "topic_id": str(topic.id),
                    "code": topic.code,
                    "name": topic.name,
                }
            )
        return refs or None

    @staticmethod
    def _object_key(
        object_code: str,
        identifier_code: str | None,
    ) -> tuple[str, str | None]:

        return object_code, identifier_code

    @staticmethod
    def _optional_str(
        value,
    ) -> str | None:

        if value is None:
            return None
        return str(value)

    @staticmethod
    def _confidence(
        value,
    ) -> float | None:

        if value is None:
            return None
        confidence = float(value)
        if confidence < 0 or confidence > 1:
            raise ValueError(
                "Knowledge confidence must be between 0 and 1",
            )
        return confidence

    @staticmethod
    def _data_type(
        value,
    ) -> str | None:

        if value is None:
            return None
        data_type = str(value)
        supported = {
            item.value
            for item in KnowledgeFieldDataType
        }
        if data_type not in supported:
            return data_type
        return KnowledgeFieldDataType(data_type).value
