from uuid import uuid4
import json

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

    assert payload["document_title"] == "Housing trends"
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
            json.dumps(
                {
                    "document_type": {
                        "code": "research_report",
                        "name": "Research report",
                        "description": None,
                        "metadata": {},
                    },
                    "topic": {
                        "code": "housing_market_trends",
                        "name": "Housing market trends",
                        "description": None,
                        "metadata": {},
                    },
                    "head": {
                        "type": "topic",
                        "code": "housing_market_trends",
                        "name": "Housing market trends",
                        "description": None,
                        "metadata": {},
                    },
                }
            )
        ),
    )

    context = await analyzer.analyze(
        ingestion_job_id=uuid4(),
        document_id=uuid4(),
    )

    assert context.document_type.code == "research_report"
    assert context.document_type.name == "Research report"
    assert context.topic.code == "housing_market_trends"
    assert context.head.type == "topic"


@pytest.mark.asyncio
async def test_analyze_rejects_document_type_string():
    analyzer = analyzer_for_response(
        {
            "document_type": "research_report",
            "topic": {
                "code": "housing_market_trends",
            },
            "head": {},
        }
    )

    with pytest.raises(
        ValueError,
        match="document_type must be an object",
    ):
        await analyzer.analyze(
            ingestion_job_id=uuid4(),
            document_id=uuid4(),
        )


@pytest.mark.asyncio
async def test_analyze_rejects_document_type_missing_code():
    analyzer = analyzer_for_response(
        {
            "document_type": {
                "name": "Research report",
                "metadata": {},
            },
            "topic": {
                "code": "housing_market_trends",
            },
            "head": {},
        }
    )

    with pytest.raises(
        ValueError,
        match="document_type code must be a non-empty string",
    ):
        await analyzer.analyze(
            ingestion_job_id=uuid4(),
            document_id=uuid4(),
        )


@pytest.mark.asyncio
async def test_analyze_rejects_old_topics_contract():
    analyzer = analyzer_for_response(
        {
            "document_type": {
                "code": "research_report",
            },
            "topics": [
                {
                    "code": "housing_market_trends",
                }
            ],
            "head": {},
        }
    )

    with pytest.raises(
        ValueError,
        match="missing topic",
    ):
        await analyzer.analyze(
            ingestion_job_id=uuid4(),
            document_id=uuid4(),
        )


@pytest.mark.asyncio
async def test_analyze_rejects_missing_topic():
    analyzer = analyzer_for_response(
        {
            "document_type": {
                "code": "research_report",
            },
            "head": {},
        }
    )

    with pytest.raises(
        ValueError,
        match="missing topic",
    ):
        await analyzer.analyze(
            ingestion_job_id=uuid4(),
            document_id=uuid4(),
        )


@pytest.mark.asyncio
async def test_analyze_rejects_topic_not_object():
    analyzer = analyzer_for_response(
        {
            "document_type": {
                "code": "research_report",
            },
            "topic": "housing_market_trends",
            "head": {},
        }
    )

    with pytest.raises(
        ValueError,
        match="topic must be an object",
    ):
        await analyzer.analyze(
            ingestion_job_id=uuid4(),
            document_id=uuid4(),
        )


@pytest.mark.asyncio
async def test_analyze_rejects_topic_missing_code():
    analyzer = analyzer_for_response(
        {
            "document_type": {
                "code": "research_report",
            },
            "topic": {
                "name": "Housing market trends",
            },
            "head": {},
        }
    )

    with pytest.raises(
        ValueError,
        match="topic code must be a non-empty string",
    ):
        await analyzer.analyze(
            ingestion_job_id=uuid4(),
            document_id=uuid4(),
        )


@pytest.mark.asyncio
async def test_analyze_rejects_head_not_object():
    analyzer = analyzer_for_response(
        {
            "document_type": {
                "code": "research_report",
            },
            "topic": {
                "code": "housing_market_trends",
            },
            "head": "housing_market_trends",
        }
    )

    with pytest.raises(
        ValueError,
        match="head must be an object",
    ):
        await analyzer.analyze(
            ingestion_job_id=uuid4(),
            document_id=uuid4(),
        )


@pytest.mark.asyncio
async def test_analyze_rejects_missing_document_type():
    analyzer = LLMDocumentStructureAnalyzer(
        extracted_asset_reader=FakeExtractedAssetReader(
            {
                "sections": [],
                "content": "short preview",
            }
        ),
        prompt_provider=FakePromptProvider(),
        llm_gateway=FakeLLMGateway(
            '{"topic": {"code": "housing_market_trends"}, "head": {}}'
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


@pytest.mark.asyncio
async def test_response_format_string_falls_back_to_json_object():
    llm_gateway = FakeLLMGateway(valid_response_content())
    analyzer = LLMDocumentStructureAnalyzer(
        extracted_asset_reader=FakeExtractedAssetReader(
            {
                "sections": [],
                "content": "short preview",
            }
        ),
        prompt_provider=FakePromptProvider(
            configuration={
                "response_format": "json_object",
            }
        ),
        llm_gateway=llm_gateway,
    )

    await analyzer.analyze(
        ingestion_job_id=uuid4(),
        document_id=uuid4(),
    )

    assert llm_gateway.response_format == {
        "type": "json_object",
    }


@pytest.mark.asyncio
async def test_response_format_json_object_is_preserved():
    response_format = {
        "type": "json_object",
    }
    llm_gateway = FakeLLMGateway(valid_response_content())
    analyzer = LLMDocumentStructureAnalyzer(
        extracted_asset_reader=FakeExtractedAssetReader(
            {
                "sections": [],
                "content": "short preview",
            }
        ),
        prompt_provider=FakePromptProvider(
            configuration={
                "response_format": response_format,
            }
        ),
        llm_gateway=llm_gateway,
    )

    await analyzer.analyze(
        ingestion_job_id=uuid4(),
        document_id=uuid4(),
    )

    assert llm_gateway.response_format is response_format


def test_uuid_title_does_not_win_over_meaningful_heading():
    payload = LLMDocumentStructureAnalyzer._build_document_payload(
        {
            "title": "550e8400-e29b-41d4-a716-446655440000",
            "file_name": "report.pdf",
            "sections": [
                {
                    "level": 1,
                    "title": "Housing market outlook",
                }
            ],
        }
    )

    assert payload["document_title"] == "Housing market outlook"


def analyzer_for_response(raw_response):
    return LLMDocumentStructureAnalyzer(
        extracted_asset_reader=FakeExtractedAssetReader(
            {
                "sections": [],
                "content": "short preview",
            }
        ),
        prompt_provider=FakePromptProvider(),
        llm_gateway=FakeLLMGateway(json.dumps(raw_response)),
    )


def valid_response_content():
    return json.dumps(
        {
            "document_type": {
                "code": "research_report",
                "metadata": {},
            },
            "topic": {
                "code": "housing_market_trends",
                "metadata": {},
            },
            "head": {},
        }
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
    def __init__(self, configuration=None):
        self.configuration = configuration or {}

    async def get_by_code(self, code):
        return Prompt(
            id=None,
            code=code,
            name=None,
            description=None,
            system_prompt="Detect document structure.",
            configuration=self.configuration,
            enabled=True,
            created_at=None,
            updated_at=None,
        )


class FakeLLMGateway:
    def __init__(self, content):
        self.content = content
        self.response_format = None
        self.user_prompt = None

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
        self.response_format = response_format
        self.user_prompt = user_prompt
        return LLMResult(
            content=self.content,
            provider_code=provider_code,
            model_code=model_code,
            response_id=None,
            finish_reason=None,
            usage={},
        )
