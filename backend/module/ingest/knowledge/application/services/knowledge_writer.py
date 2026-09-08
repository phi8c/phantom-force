from typing import Any
import logging

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


logger = logging.getLogger(__name__)


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

        raw_response = self._validate_response(
            dict(request.raw_response or {}),
        )
        knowledge_space_id = request.knowledge_space_id
        information_written = 0

        logger.info(
            "knowledge write_start knowledge_space_id=%s document_id=%s chunk_id=%s model=%s information=%s",
            knowledge_space_id,
            request.document_id,
            request.chunk_id,
            request.model_name,
            len(raw_response["information"]),
        )

        document_types = await self._upsert_document_types(
            knowledge_space_id,
            raw_response,
        )
        information_types = await self._upsert_information_types(
            knowledge_space_id,
            raw_response,
        )
        await self._upsert_information_fields(
            knowledge_space_id,
            raw_response,
        )
        objects = await self._upsert_objects(
            knowledge_space_id,
            raw_response,
        )
        topics = await self._upsert_topics(
            knowledge_space_id,
            raw_response,
        )

        for ordinal, item in enumerate(raw_response["information"]):
            summary = item.get("summary")
            if not summary:
                raise ValueError(
                    "Knowledge information item missing summary",
                )

            information_type_id = None
            information_type = item.get(
                "information_type",
            )
            if information_type:
                resolved_information_type = information_types.get(
                    str(information_type),
                )
                if resolved_information_type is not None:
                    information_type_id = (
                        resolved_information_type.id
                    )

            source_confidence = self._confidence(
                item.get("confidence"),
            )

            source_identity = {
                "document_id": str(request.document_id),
                "chunk_id": str(request.chunk_id),
                "model_name": request.model_name,
                "ordinal": ordinal,
            }

            await self._repository.upsert_information(
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
                            **source_identity,
                            "confidence": source_confidence,
                        }
                    ],
                    confidence=source_confidence,
                    raw_model_output=raw_response,
                    metadata={
                        "model_name": request.model_name,
                        "document_type_codes": [
                            document_type.code
                            for document_type
                            in document_types.values()
                        ],
                    },
                    created_at=None,
                    updated_at=None,
                ),
                source_identity=source_identity,
            )
            information_written += 1

        logger.info(
            "knowledge write_done knowledge_space_id=%s document_id=%s chunk_id=%s model=%s document_types=%s information_types=%s objects=%s topics=%s information=%s",
            knowledge_space_id,
            request.document_id,
            request.chunk_id,
            request.model_name,
            len(document_types),
            len(information_types),
            len(objects),
            len(topics),
            information_written,
        )

    async def _upsert_document_types(
        self,
        knowledge_space_id,
        raw_response: dict[str, Any],
    ):

        result = {}
        item = raw_response["document_type"]
        if item is not None:
            code = item.get("code")
            if not code:
                raise ValueError(
                    "document_type missing code",
                )
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
        for item in raw_response["information_types"]:
            code = item.get("code")
            if not code:
                raise ValueError(
                    "information_types item missing code",
                )
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

        for item in raw_response["information_fields"]:
            code = item.get("code")
            if not code:
                raise ValueError(
                    "information_fields item missing code",
                )
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
        for item in raw_response["objects"]:
            object_code = item.get("object_code")
            if not object_code:
                raise ValueError(
                    "objects item missing object_code",
                )
            entity = await self._repository.upsert_object(
                KnowledgeObject(
                    id=None,
                    knowledge_space_id=knowledge_space_id,
                    object_code=str(object_code),
                    identifier_code=self._optional_str(
                        item.get("identifier_code"),
                    ),
                    object_name=item.get("object_name"),
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
                    entity,
                )
            ] = entity
        return result

    async def _upsert_topics(
        self,
        knowledge_space_id,
        raw_response: dict[str, Any],
    ):

        result = {}
        for item in raw_response["topics"]:
            code = item.get("code")
            if not code:
                raise ValueError(
                    "topics item missing code",
                )
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
    def _validate_response(
        raw_response: dict[str, Any],
    ) -> dict[str, Any]:

        required_types = {
            "sensitivity": dict,
            "document_type": dict,
            "objects": list,
            "information_types": list,
            "information_fields": list,
            "topics": list,
            "information": list,
        }

        for key, expected_type in required_types.items():
            if key not in raw_response:
                raise ValueError(
                    f"Knowledge response missing {key}",
                )
            if not isinstance(
                raw_response[key],
                expected_type,
            ):
                raise ValueError(
                    "Knowledge response field "
                    f"{key} must be {expected_type.__name__}",
                )

        sensitivity = raw_response["sensitivity"]
        level = sensitivity.get("level")
        if isinstance(level, bool) or not isinstance(level, int):
            raise ValueError(
                "Knowledge response sensitivity.level must be integer",
            )
        if level < 1:
            raise ValueError(
                "Knowledge response sensitivity.level must be at least 1",
            )
        if not isinstance(
            sensitivity.get("description"),
            str,
        ):
            raise ValueError(
                "Knowledge response sensitivity.description must be string",
            )

        for key in (
            "objects",
            "information_types",
            "information_fields",
            "topics",
            "information",
        ):
            for item in raw_response[key]:
                if not isinstance(item, dict):
                    raise ValueError(
                        f"Knowledge response {key} items must be objects",
                    )

        for item in raw_response["information"]:
            information_type = item.get("information_type")
            if (
                information_type is not None
                and not isinstance(information_type, str)
            ):
                raise ValueError(
                    "Knowledge response information.information_type must be string",
                )

            for ref_field in (
                "object_refs",
                "topic_refs",
            ):
                refs = item.get(ref_field)
                if refs is None:
                    continue
                if not isinstance(refs, list):
                    raise ValueError(
                        f"information.{ref_field} must be a list",
                    )
                for ref in refs:
                    if not isinstance(ref, str):
                        raise ValueError(
                            f"information.{ref_field} item must be a string",
                        )

        return raw_response

    @classmethod
    def _object_refs(
        cls,
        item: dict[str, Any],
        objects,
    ) -> list[dict[str, Any]] | None:

        refs = []
        object_refs = item.get("object_refs")
        if object_refs is None:
            return None
        if not isinstance(object_refs, list):
            raise ValueError(
                "information.object_refs must be a list",
            )
        for ref in object_refs:
            if not isinstance(ref, str):
                raise ValueError(
                    "information.object_refs item must be a string",
                )
            object_ref = objects.get(str(ref))
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
        topic_values = item.get("topic_refs")
        if topic_values is None:
            return None
        if not isinstance(topic_values, list):
            raise ValueError(
                "information.topic_refs must be a list",
            )
        for ref in topic_values:
            if not isinstance(ref, str):
                raise ValueError(
                    "information.topic_refs item must be a string",
                )
            topic = topics.get(ref)
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
        item: KnowledgeObject,
    ) -> str:

        return item.identifier_code or item.object_code

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
