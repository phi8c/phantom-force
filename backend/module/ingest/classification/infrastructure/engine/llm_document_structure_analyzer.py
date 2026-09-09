import json
import logging
from typing import Any
from uuid import UUID

from module.ai.llm.composition import LLMGateway
from module.ingest.chunking.composition import (
    ExtractedAssetReader,
)
from module.ingest.classification.domain.entities.document_context import (
    DocumentContext,
    DocumentContextDocumentType,
    DocumentContextHead,
    DocumentContextTopic,
)
from module.ingest.classification.domain.contracts.document_structure_analyzer import (
    DocumentStructureAnalyzer as DocumentStructureAnalyzerContract,
)
from module.prompt.composition import PromptProvider


logger = logging.getLogger(__name__)

MAX_FALLBACK_TEXT_CHARS = 4000


class LLMDocumentStructureAnalyzer(
    DocumentStructureAnalyzerContract,
):

    def __init__(
        self,
        extracted_asset_reader: ExtractedAssetReader,
        prompt_provider: PromptProvider,
        llm_gateway: LLMGateway,
    ):
        self._extracted_asset_reader = extracted_asset_reader
        self._prompt_provider = prompt_provider
        self._llm_gateway = llm_gateway

    async def analyze(
        self,
        *,
        ingestion_job_id: UUID,
        document_id: UUID,
    ) -> DocumentContext:

        extracted = await self._load_extracted_json(
            ingestion_job_id=ingestion_job_id,
            document_id=document_id,
        )

        payload = self._build_document_payload(
            extracted,
        )

        prompt = await self._prompt_provider.get_by_code(
            "ingest.knowledge.detect_document_heads",
        )
        if prompt is None:
            raise ValueError(
                "Document structure prompt not found or disabled",
            )

        config = dict(prompt.configuration or {})
        response_format = config.pop(
            "response_format",
            None,
        )
        response_format = self._response_format_from_config(
            response_format,
        )

        llm_result = await self._llm_gateway.generate(
            provider_code="azure_openai",
            model_code="gpt-5.1",
            system_prompt=prompt.system_prompt,
            user_prompt=self._build_user_prompt(payload),
            response_format=response_format,
            config=config,
        )

        if not llm_result.content:
            raise ValueError(
                "Empty document structure response",
            )

        try:
            raw_response = json.loads(llm_result.content)
        except json.JSONDecodeError as exc:
            raise ValueError(
                "Invalid document structure JSON response",
            ) from exc

        context = self._parse_document_context(
            raw_response,
        )

        logger.info(
            "document_structure analyzed document_id=%s model=%s "
            "document_type=%s topic=%s head=%s",
            document_id,
            llm_result.model_code,
            context.document_type.code,
            context.topic.code,
            {
                "type": context.head.type,
                "code": context.head.code,
            },
        )

        return context

    async def _load_extracted_json(
        self,
        *,
        ingestion_job_id: UUID,
        document_id: UUID,
    ) -> dict[str, Any]:

        asset = await self._extracted_asset_reader.open_extracted(
            ingestion_job_id=ingestion_job_id,
            document_id=document_id,
        )

        content = bytearray()
        async for chunk in asset.content:
            content.extend(chunk)

        parsed = json.loads(
            content.decode("utf-8"),
        )
        if not isinstance(parsed, dict):
            raise ValueError(
                "Extracted asset must contain a JSON object",
            )
        return parsed

    @classmethod
    def _build_document_payload(
        cls,
        extracted: dict[str, Any],
    ) -> dict[str, Any]:

        headings = cls.extract_headings(
            extracted.get("sections", []),
        )
        payload = {
            "file_name": cls._optional_str(
                extracted.get("file_name"),
            ),
            "document_title": cls._document_title(
                extracted,
                headings,
            ),
            "headings": headings,
        }

        if not headings:
            payload["fallback_text"] = cls.fallback_text(
                extracted,
            )

        return payload

    @staticmethod
    def extract_headings(
        sections,
    ) -> list[dict[str, Any]]:

        headings: list[dict[str, Any]] = []

        def visit(items):
            if not isinstance(items, list):
                return

            for item in items:
                if not isinstance(item, dict):
                    continue

                title = item.get("title")
                if isinstance(title, str) and title.strip():
                    title = title.strip()
                    if title.upper() != "ROOT":
                        headings.append(
                            {
                                "level": item.get("level"),
                                "title": title,
                            }
                        )

                visit(item.get("children"))

        visit(sections)
        return headings

    @classmethod
    def fallback_text(
        cls,
        extracted: dict[str, Any],
    ) -> str:

        parts: list[str] = []

        def collect(value):
            if sum(len(part) for part in parts) >= MAX_FALLBACK_TEXT_CHARS:
                return
            if isinstance(value, str) and value.strip():
                parts.append(value.strip())
                return
            if isinstance(value, dict):
                for key in (
                    "content",
                    "text",
                    "aggregated_content",
                ):
                    collect(value.get(key))
                collect(value.get("children"))
                return
            if isinstance(value, list):
                for item in value:
                    collect(item)

        collect(extracted.get("content"))
        collect(extracted.get("aggregated_content"))
        collect(extracted.get("sections"))

        return "\n".join(parts)[:MAX_FALLBACK_TEXT_CHARS]

    @classmethod
    def _document_title(
        cls,
        extracted: dict[str, Any],
        headings: list[dict[str, Any]],
    ) -> str | None:

        for key in (
            "document_title",
            "title",
        ):
            value = cls._optional_str(extracted.get(key))
            if cls._is_meaningful_title(value):
                return value

        if headings:
            value = cls._optional_str(headings[0].get("title"))
            if cls._is_meaningful_title(value):
                return value

        value = cls._optional_str(extracted.get("file_name"))
        if value:
            return value

        return None

    @staticmethod
    def _build_user_prompt(
        payload: dict[str, Any],
    ) -> str:

        return json.dumps(
            {
                **payload,
                "response_contract": {
                    "document_type": {
                        "code": "string",
                        "name": "string or null",
                        "description": "string or null",
                        "metadata": "object",
                    },
                    "topic": {
                        "code": "string",
                        "name": "string or null",
                        "description": "string or null",
                        "metadata": "object",
                    },
                    "head": {
                        "type": "string or null",
                        "code": "string or null",
                        "name": "string or null",
                        "description": "string or null",
                        "metadata": "object",
                    },
                },
            },
            ensure_ascii=False,
        )

    @classmethod
    def _parse_document_context(
        cls,
        raw_response: dict[str, Any],
    ) -> DocumentContext:

        if not isinstance(raw_response, dict):
            raise ValueError(
                "Document structure response must be a JSON object",
            )

        document_type = raw_response.get("document_type")
        topic = raw_response.get("topic")
        head = raw_response.get("head")

        if "document_type" not in raw_response:
            cls._raise_contract_error(
                "missing_document_type",
                "Document structure response missing document_type",
            )
        if not isinstance(document_type, dict):
            cls._raise_contract_error(
                "document_type_not_object",
                "Document structure response document_type must be an object",
                field="document_type",
                actual_type=type(document_type).__name__,
            )
        if "topic" not in raw_response:
            cls._raise_contract_error(
                "missing_topic",
                "Document structure response missing topic",
            )
        if not isinstance(topic, dict):
            cls._raise_contract_error(
                "topic_not_object",
                "Document structure response topic must be an object",
                field="topic",
                actual_type=type(topic).__name__,
            )
        if "head" not in raw_response:
            cls._raise_contract_error(
                "head_missing",
                "Document structure response missing head",
            )
        if not isinstance(head, dict):
            cls._raise_contract_error(
                "head_not_object",
                "Document structure response head must be an object",
                field="head",
                actual_type=type(head).__name__,
            )

        document_type_code = cls._required_code(
            document_type,
            "document_type",
            reason="missing_invalid_document_type_code",
            field="document_type.code",
        )

        parsed_topic = DocumentContextTopic(
            code=cls._required_code(
                topic,
                "topic",
                reason="invalid_topic_code",
                field="topic.code",
            ),
            name=cls._optional_str(topic.get("name")),
            description=cls._optional_str(
                topic.get("description"),
            ),
            metadata=cls._metadata(
                topic,
                field_name="topic.metadata",
            ),
        )

        return DocumentContext(
            document_type=DocumentContextDocumentType(
                code=document_type_code,
                name=cls._optional_str(document_type.get("name")),
                description=cls._optional_str(
                    document_type.get("description"),
                ),
                metadata=cls._metadata(
                    document_type,
                    field_name="document_type.metadata",
                ),
            ),
            topic=parsed_topic,
            head=DocumentContextHead(
                type=cls._optional_str(head.get("type")),
                code=cls._optional_str(head.get("code")),
                name=cls._optional_str(head.get("name")),
                description=cls._optional_str(
                    head.get("description"),
                ),
                metadata=cls._metadata(
                    head,
                    field_name="head.metadata",
                ),
            ),
        )

    @staticmethod
    def _required_code(
        item: dict[str, Any],
        field_name: str,
        *,
        reason: str | None = None,
        field: str | None = None,
        index: int | None = None,
    ) -> str:

        code = item.get("code")
        if not isinstance(code, str) or not code.strip():
            LLMDocumentStructureAnalyzer._raise_contract_error(
                reason or f"missing_invalid_{field_name}_code",
                f"Document structure response {field_name} code "
                "must be a non-empty string",
                field=field or f"{field_name}.code",
                index=index,
                actual_type=type(code).__name__,
            )
        return code.strip()

    @staticmethod
    def _response_format_from_config(
        response_format: Any,
    ) -> dict[str, Any]:

        json_object_format = {
            "type": "json_object",
        }

        if response_format is None:
            return json_object_format

        if not isinstance(response_format, dict):
            logger.warning(
                "document_structure response_format_ignored reason=%s actual_type=%s",
                "invalid_response_format_type",
                type(response_format).__name__,
            )
            return json_object_format

        if response_format.get("type") == "json_object":
            return response_format

        logger.warning(
            "document_structure response_format_ignored reason=%s response_format=%s",
            "invalid_response_format",
            response_format,
        )
        return json_object_format

    @staticmethod
    def _raise_contract_error(
        reason: str,
        message: str,
        *,
        field: str | None = None,
        index: int | None = None,
        actual_type: str | None = None,
    ) -> None:

        logger.error(
            "document_structure contract_invalid reason=%s field=%s index=%s actual_type=%s",
            reason,
            field,
            index,
            actual_type,
        )
        raise ValueError(message)

    @staticmethod
    def _is_meaningful_title(
        value: str | None,
    ) -> bool:

        if not value:
            return False

        try:
            UUID(value)
            return False
        except ValueError:
            pass

        lowered = value.strip().lower()
        if lowered in {
            "untitled",
            "unknown",
            "none",
            "null",
            "document",
        }:
            return False

        technical_chars = sum(
            1
            for char in value
            if char.isdigit() or char in {"-", "_", "."}
        )
        if technical_chars >= max(4, len(value) // 2):
            return False

        return any(char.isalpha() for char in value)

    @staticmethod
    def _metadata(
        item: dict[str, Any],
        *,
        field_name: str,
        index: int | None = None,
    ) -> dict[str, Any]:

        metadata = item.get("metadata", {})
        if not isinstance(metadata, dict):
            LLMDocumentStructureAnalyzer._raise_contract_error(
                "invalid_metadata",
                "Document structure response metadata must be an object",
                field=field_name,
                index=index,
                actual_type=type(metadata).__name__,
            )
        return metadata

    @staticmethod
    def _optional_str(
        value,
    ) -> str | None:

        if value is None:
            return None
        value = str(value).strip()
        return value or None
