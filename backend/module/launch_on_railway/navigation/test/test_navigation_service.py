from uuid import uuid4

import pytest

from module.ingest.knowledge.application.dtos import (
    KnowledgeDiscoveryResult,
)
from module.launch_on_railway.knowledge_selection.application.dtos import (
    KnowledgeSelectionResult,
)
from module.launch_on_railway.navigation.application.services.navigation_service import (
    NavigationService,
)
from module.launch_on_railway.query_analysis.application.dtos.response.query_analysis_result import (
    KnowledgeRequest,
    QueryAnalysisResult,
)


@pytest.mark.asyncio
async def test_navigation_uses_grouped_knowledge_requests_for_discovery():
    reader = RecordingKnowledgeReader()
    selector = RecordingKnowledgeSelector()
    service = NavigationService(
        knowledge_reader=reader,
        knowledge_selector=selector,
    )
    knowledge_space_id = uuid4()

    await service.navigate(
        knowledge_space_id=knowledge_space_id,
        question="Compare browser cache policies",
        analysis=QueryAnalysisResult(
            intent="compare",
            knowledge_requests=[
                KnowledgeRequest(
                    need="Compare browser cache policies",
                    document_type_seeds=[
                        "technical_document",
                    ],
                    head_seeds=[
                        "cache section",
                    ],
                    topic_seeds=[
                        "cache_policy",
                    ],
                    object_seeds=[
                        "chrome",
                        "edge",
                    ],
                    identifier_seeds=[
                        "stable",
                    ],
                    information_type_seeds=[
                        "policy",
                    ],
                    information_field_seeds=[
                        "ttl",
                    ],
                    constraints={
                        "scope": "comparison",
                    },
                )
            ],
            raw_response={},
        ),
    )

    discovery_request = reader.discovery_requests[0]
    assert discovery_request.knowledge_space_id == knowledge_space_id
    assert discovery_request.seeds == []
    assert len(discovery_request.items) == 1

    item = discovery_request.items[0]
    assert item.request_id == "knowledge_1"
    assert item.need == "Compare browser cache policies"
    assert item.document_type_seeds == [
        "technical_document",
    ]
    assert item.head_seeds == [
        "cache section",
    ]
    assert item.topic_seeds == [
        "cache_policy",
    ]
    assert item.object_seeds == [
        "chrome",
        "edge",
    ]
    assert item.identifier_seeds == [
        "stable",
    ]
    assert item.information_type_seeds == [
        "policy",
    ]
    assert item.information_field_seeds == [
        "ttl",
    ]
    assert item.constraints == {
        "scope": "comparison",
    }
    assert selector.knowledge_candidates is None


class RecordingKnowledgeReader:
    def __init__(self):
        self.discovery_requests = []

    async def discover(self, request):
        self.discovery_requests.append(request)
        return KnowledgeDiscoveryResult()


class RecordingKnowledgeSelector:
    def __init__(self):
        self.knowledge_candidates = None

    async def select(self, *, question, knowledge_candidates):
        self.knowledge_candidates = knowledge_candidates
        return KnowledgeSelectionResult()
