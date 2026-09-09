from uuid import uuid4

import pytest

from module.ai.llm.domain.value_objects.llm_result import (
    LLMResult,
)
from module.ingest.chunking.composition import ExtractedAsset
from module.ingest.classification.infrastructure.engine.llm_document_structure_analyzer import (
    LLMDocumentStructureAnalyzer,
    MAX_FALLBACK_TEXT_CHARS,
)
from module.prompt.domain.entities.prompt import Prompt


def test_extract_headings_supports_nested_children():
    headings = LLMDocumentStructureAnalyzer.extract_headings(
        [
            {
                "level": 0,
                "title": "ROOT",
            },
            {
                "level": 1,
                "title": "Overview",
                "children": [
                    {
                        "level": 2,
                        "title": "Market",
                    }
                ],
            }
        ]
    )

    assert headings == [
        {
            "level": 1,
            "title": "Overview",
        },
        {
            "level": 2,
            "title": "Market",
        },
    ]


def test_document_payload_uses_headings_without_content_fallback():
    payload = LLMDocumentStructureAnalyzer._build_document_payload(
        {
            "file_name": "report.pdf",
            "sections": [
                {
                    "level": 1,
                    "title": "Housing trends",
                    "aggregated_content": "large body",
                }
            ],
        }
    )

    assert payload["document_title"] == "report.pdf"
    assert payload["headings"] == [
        {
            "level": 1,
            "title": "Housing trends",
        }
    ]
    assert "fallback_text" not in payload


def test_document_payload_fallback_is_limited_when_no_headings():
    payload = LLMDocumentStructureAnalyzer._build_document_payload(
        {
            "title": "Untitled",
            "sections": [
                {
                    "content": "x" * (MAX_FALLBACK_TEXT_CHARS + 100),
                }
            ],
        }
    )

    assert payload["headings"] == []
    assert len(payload["fallback_text"]) == MAX_FALLBACK_TEXT_CHARS


@pytest.mark.asyncio
async def test_analyze_validates_required_response_contract():
    analyzer = LLMDocumentStructureAnalyzer(
        extracted_asset_reader=FakeExtractedAssetReader(
            {
                "file_name": "report.pdf",
                "sections": [
                    {
                        "level": 1,
                        "title": "Housing trends",
                    }
                ],
            }
        ),
        prompt_provider=FakePromptProvider(),
        llm_gateway=FakeLLMGateway(
            '{"document_type": {"code": "research_report"}, "topics": [], "head": {}}'
        ),
    )

    context = await analyzer.analyze(
        ingestion_job_id=uuid4(),
        document_id=uuid4(),
    )

    assert context.document_type.code == "research_report"
    assert context.topics == []
    assert context.head.type is None


@pytest.mark.asyncio
async def test_analyze_rejects_invalid_response_contract():
    analyzer = LLMDocumentStructureAnalyzer(
        extracted_asset_reader=FakeExtractedAssetReader(
            {
                "sections": [],
                "content": "short preview",
            }
        ),
        prompt_provider=FakePromptProvider(),
        llm_gateway=FakeLLMGateway(
            '{"topics": [], "head": {}}'
        ),
    )

    with pytest.raises(
        ValueError,
        match="document_type",
    ):
        await analyzer.analyze(
            ingestion_job_id=uuid4(),
            document_id=uuid4(),
        )


class FakeExtractedAssetReader:
    def __init__(self, payload):
        self.payload = payload

    async def open_extracted(self, *, ingestion_job_id, document_id):
        return ExtractedAsset(
            document_id=document_id,
            content=self._content(),
            content_type="application/json",
            size_bytes=None,
        )

    async def _content(self):
        yield __import__("json").dumps(self.payload).encode("utf-8")


class FakePromptProvider:
    async def get_by_code(self, code):
        return Prompt(
            id=None,
            code=code,
            name=None,
            description=None,
            system_prompt="Detect document structure.",
            configuration={},
            enabled=True,
            created_at=None,
            updated_at=None,
        )


class FakeLLMGateway:
    def __init__(self, content):
        self.content = content

    async def generate(
        self,
        *,
        provider_code,
        model_code,
        system_prompt,
        user_prompt,
        response_format=None,
        config=None,
    ):
        return LLMResult(
            content=self.content,
            provider_code=provider_code,
            model_code=model_code,
            response_id=None,
            finish_reason=None,
            usage={},
        )
