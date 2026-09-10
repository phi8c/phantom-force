from uuid import uuid4

import pytest

from module.ingest.knowledge.application.dtos import (
    KnowledgeDiscoveredRequest,
    KnowledgeDiscoveryResult,
    KnowledgeMatchedEntryPoints,
    KnowledgeSearchItem,
    KnowledgeSearchResult,
)
from module.launch_on_railway.knowledge_selection.application.dtos import (
    KnowledgeSelection,
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


@pytest.mark.asyncio
async def test_navigation_retrieves_selected_requests_and_dedupes_information():
    information_id = uuid4()
    reader = RecordingKnowledgeReader(
        discovery_result=KnowledgeDiscoveryResult(
            requests=[
                KnowledgeDiscoveredRequest(
                    request_id="knowledge_1",
                    matched_entry_points=KnowledgeMatchedEntryPoints(),
                ),
                KnowledgeDiscoveredRequest(
                    request_id="knowledge_2",
                    matched_entry_points=KnowledgeMatchedEntryPoints(),
                ),
                KnowledgeDiscoveredRequest(
                    request_id="knowledge_3",
                    matched_entry_points=KnowledgeMatchedEntryPoints(),
                ),
            ],
        ),
        retrieval_results={
            "knowledge_1": KnowledgeSearchResult(
                items=[
                    KnowledgeSearchItem(
                        information_id=information_id,
                        information_type_code="requirement",
                        summary="Shared requirement",
                        data={},
                        object_refs=[],
                        topic_refs=[],
                        source_refs=[],
                        confidence=0.9,
                    )
                ],
            ),
            "knowledge_3": KnowledgeSearchResult(
                items=[
                    KnowledgeSearchItem(
                        information_id=information_id,
                        information_type_code="requirement",
                        summary="Duplicate requirement",
                        data={},
                        object_refs=[],
                        topic_refs=[],
                        source_refs=[],
                        confidence=0.8,
                    )
                ],
            ),
        },
    )
    selector = RecordingKnowledgeSelector(
        selections=[
            KnowledgeSelection(
                request_id="knowledge_1",
                topic_codes=[
                    "topic_a",
                ],
            ),
            KnowledgeSelection(
                request_id="knowledge_3",
                topic_codes=[
                    "topic_c",
                ],
            ),
        ],
    )
    service = NavigationService(
        knowledge_reader=reader,
        knowledge_selector=selector,
    )

    result = await service.navigate(
        knowledge_space_id=uuid4(),
        question="Compare topics",
        analysis=QueryAnalysisResult(
            intent="compare",
            knowledge_requests=[
                KnowledgeRequest(need="Need A"),
                KnowledgeRequest(need="Need B"),
                KnowledgeRequest(need="Need C"),
            ],
            raw_response={},
        ),
    )

    assert [
        item.request_id
        for item in reader.discovery_requests[0].items
    ] == [
        "knowledge_1",
        "knowledge_2",
        "knowledge_3",
    ]
    assert [
        item.request_id
        for item in selector.knowledge_candidates
    ] == [
        "knowledge_1",
        "knowledge_2",
        "knowledge_3",
    ]
    assert [
        request.selection.request_id
        for request in reader.retrieval_requests
    ] == [
        "knowledge_1",
        "knowledge_3",
    ]
    assert [
        item.information_id
        for item in result.items
    ] == [
        str(information_id),
    ]


class RecordingKnowledgeReader:
    def __init__(
        self,
        discovery_result=None,
        retrieval_results=None,
    ):
        self.discovery_requests = []
        self.retrieval_requests = []
        self.discovery_result = discovery_result or KnowledgeDiscoveryResult()
        self.retrieval_results = retrieval_results or {}

    async def discover(self, request):
        self.discovery_requests.append(request)
        return self.discovery_result

    async def retrieve(self, request):
        self.retrieval_requests.append(request)
        return self.retrieval_results.get(
            request.selection.request_id,
            KnowledgeSearchResult(),
        )


class RecordingKnowledgeSelector:
    def __init__(self, selections=None):
        self.knowledge_candidates = None
        self.selections = selections or []

    async def select(self, *, question, knowledge_candidates):
        self.knowledge_candidates = knowledge_candidates
        return KnowledgeSelectionResult(
            selections=self.selections,
        )
