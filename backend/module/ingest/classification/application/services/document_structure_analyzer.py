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


class DocumentStructureAnalyzer(
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
            {"type": "json_object"},
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
            "document_type=%s topics=%s head=%s",
            document_id,
            llm_result.model_code,
            context.document_type.code,
            [topic.code for topic in context.topics],
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
            "file_name",
        ):
            value = cls._optional_str(extracted.get(key))
            if value:
                return value

        if headings:
            return cls._optional_str(headings[0].get("title"))

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
                    "topics": {
                        "type": "array",
                        "item": {
                            "code": "string",
                            "name": "string or null",
                            "description": "string or null",
                            "metadata": "object",
                        },
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
        topics = raw_response.get("topics")
        head = raw_response.get("head")

        if not isinstance(document_type, dict):
            raise ValueError(
                "Document structure response missing document_type",
            )
        if not isinstance(topics, list):
            raise ValueError(
                "Document structure response topics must be a list",
            )
        if not isinstance(head, dict):
            raise ValueError(
                "Document structure response missing head",
            )

        document_type_code = cls._required_code(
            document_type,
            "document_type",
        )

        parsed_topics = []
        for topic in topics:
            if not isinstance(topic, dict):
                raise ValueError(
                    "Document structure topics items must be objects",
                )
            parsed_topics.append(
                DocumentContextTopic(
                    code=cls._required_code(topic, "topics"),
                    name=cls._optional_str(topic.get("name")),
                    description=cls._optional_str(
                        topic.get("description"),
                    ),
                    metadata=cls._metadata(topic),
                )
            )

        return DocumentContext(
            document_type=DocumentContextDocumentType(
                code=document_type_code,
                name=cls._optional_str(document_type.get("name")),
                description=cls._optional_str(
                    document_type.get("description"),
                ),
                metadata=cls._metadata(document_type),
            ),
            topics=parsed_topics,
            head=DocumentContextHead(
                type=cls._optional_str(head.get("type")),
                code=cls._optional_str(head.get("code")),
                name=cls._optional_str(head.get("name")),
                description=cls._optional_str(
                    head.get("description"),
                ),
                metadata=cls._metadata(head),
            ),
        )

    @staticmethod
    def _required_code(
        item: dict[str, Any],
        field_name: str,
    ) -> str:

        code = item.get("code")
        if not isinstance(code, str) or not code.strip():
            raise ValueError(
                f"Document structure {field_name} missing code",
            )
        return code.strip()

    @staticmethod
    def _metadata(
        item: dict[str, Any],
    ) -> dict[str, Any]:

        metadata = item.get("metadata", {})
        if not isinstance(metadata, dict):
            return {}
        return metadata

    @staticmethod
    def _optional_str(
        value,
    ) -> str | None:

        if value is None:
            return None
        value = str(value).strip()
        return value or None
