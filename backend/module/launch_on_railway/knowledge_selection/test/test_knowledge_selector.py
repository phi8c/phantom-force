import json

from module.ingest.knowledge.application.dtos import (
    KnowledgeCodeStructure,
    KnowledgeDiscoveredRequest,
    KnowledgeMatchedEntryPoints,
    KnowledgeObjectStructure,
)
from module.launch_on_railway.knowledge_selection.application.services.knowledge_selector import (
    KnowledgeSelector,
)


def test_build_user_prompt_uses_knowledge_candidates_contract():
    candidate = KnowledgeDiscoveredRequest(
        request_id="knowledge_1",
        need="Compare cache policies",
        original_seeds={
            "topic_seeds": [
                "cache_policy",
            ],
        },
        matched_entry_points=KnowledgeMatchedEntryPoints(
            objects=[
                KnowledgeObjectStructure(
                    object_code="chrome",
                    identifier_code="stable",
                ),
            ],
            information_types=[
                KnowledgeCodeStructure(
                    code="policy",
                    name="Policy",
                ),
            ],
            topics=[
                KnowledgeCodeStructure(
                    code="cache_policy",
                    name="Cache policy",
                ),
            ],
            fields=[
                KnowledgeCodeStructure(
                    code="ttl",
                    name="TTL",
                    data_type="number",
                ),
            ],
        ),
        available_information_types=[
            KnowledgeCodeStructure(
                code="policy",
                name="Policy",
            ),
        ],
        available_topics=[
            KnowledgeCodeStructure(
                code="cache_policy",
                name="Cache policy",
            ),
        ],
        available_fields=[
            KnowledgeCodeStructure(
                code="ttl",
                name="TTL",
                data_type="number",
            ),
        ],
    )

    payload = json.loads(
        KnowledgeSelector._build_user_prompt(
            question="Compare cache policies",
            knowledge_candidates=[
                candidate,
            ],
        )
    )

    assert "candidate_seeds" not in payload
    assert payload["knowledge_candidates"][0]["request_id"] == "knowledge_1"
    assert payload["knowledge_candidates"][0]["need"] == (
        "Compare cache policies"
    )
    assert payload["knowledge_candidates"][0]["original_seeds"] == {
        "topic_seeds": [
            "cache_policy",
        ],
    }
    assert payload["knowledge_candidates"][0]["matched_entry_points"][
        "fields"
    ][0]["code"] == "ttl"
    assert payload["response_contract"]["selections"]["item"][
        "request_id"
    ] == "string from knowledge_candidates"


def test_parse_selections_accepts_request_id_and_validates_candidates():
    candidate = KnowledgeDiscoveredRequest(
        request_id="knowledge_1",
        matched_entry_points=KnowledgeMatchedEntryPoints(),
        available_information_types=[
            KnowledgeCodeStructure(
                code="policy",
                name="Policy",
            ),
        ],
        available_topics=[
            KnowledgeCodeStructure(
                code="cache_policy",
                name="Cache policy",
            ),
        ],
        available_fields=[
            KnowledgeCodeStructure(
                code="ttl",
                name="TTL",
            ),
        ],
    )

    selections = KnowledgeSelector._parse_selections(
        [
            {
                "request_id": "knowledge_1",
                "information_type_codes": [
                    "policy",
                ],
                "topic_codes": [
                    "cache_policy",
                ],
                "field_codes": [
                    "ttl",
                ],
                "constraints": {
                    "scope": "comparison",
                },
            },
            {
                "request_id": "unknown",
                "information_type_codes": [
                    "policy",
                ],
            },
            {
                "request_id": "knowledge_1",
                "information_type_codes": [
                    "unknown",
                ],
                "topic_codes": [],
                "field_codes": [],
            },
        ],
        knowledge_candidates=[
            candidate,
        ],
    )

    assert len(selections) == 1
    assert selections[0].request_id == "knowledge_1"
    assert selections[0].information_type_codes == [
        "policy",
    ]
    assert selections[0].topic_codes == [
        "cache_policy",
    ]
    assert selections[0].field_codes == [
        "ttl",
    ]


def test_parse_selections_keeps_topic_when_other_codes_are_invalid():
    candidate = KnowledgeDiscoveredRequest(
        request_id="knowledge_1",
        matched_entry_points=KnowledgeMatchedEntryPoints(),
        available_information_types=[KnowledgeCodeStructure(code="policy")],
        available_topics=[KnowledgeCodeStructure(code="cache_policy")],
        available_fields=[KnowledgeCodeStructure(code="ttl")],
    )

    selections = KnowledgeSelector._parse_selections(
        [
            {
                "request_id": "knowledge_1",
                "information_type_codes": ["policy", "unknown_type"],
                "topic_codes": ["cache_policy"],
                "field_codes": ["ttl", "policy"],
            }
        ],
        knowledge_candidates=[candidate],
    )

    assert len(selections) == 1
    assert selections[0].topic_codes == ["cache_policy"]
    assert selections[0].information_type_codes == ["policy"]
    assert selections[0].field_codes == ["ttl"]


def test_parse_selections_can_select_subset_and_multiple_topics():
    candidates = [
        KnowledgeDiscoveredRequest(
            request_id="knowledge_1",
            matched_entry_points=KnowledgeMatchedEntryPoints(),
            available_topics=[
                KnowledgeCodeStructure(
                    code="topic_a",
                    name="Topic A",
                ),
                KnowledgeCodeStructure(
                    code="topic_b",
                    name="Topic B",
                ),
            ],
        ),
        KnowledgeDiscoveredRequest(
            request_id="knowledge_2",
            matched_entry_points=KnowledgeMatchedEntryPoints(),
            available_topics=[
                KnowledgeCodeStructure(
                    code="topic_c",
                    name="Topic C",
                ),
            ],
        ),
        KnowledgeDiscoveredRequest(
            request_id="knowledge_3",
            matched_entry_points=KnowledgeMatchedEntryPoints(),
            available_topics=[
                KnowledgeCodeStructure(
                    code="topic_d",
                    name="Topic D",
                ),
            ],
        ),
    ]

    selections = KnowledgeSelector._parse_selections(
        [
            {
                "request_id": "knowledge_1",
                "information_type_codes": [],
                "topic_codes": [
                    "topic_a",
                    "topic_b",
                ],
                "field_codes": [],
            },
            {
                "request_id": "knowledge_3",
                "information_type_codes": [],
                "topic_codes": [
                    "topic_d",
                ],
                "field_codes": [],
            },
        ],
        knowledge_candidates=candidates,
    )

    assert [
        selection.request_id
        for selection in selections
    ] == [
        "knowledge_1",
        "knowledge_3",
    ]
    assert selections[0].topic_codes == [
        "topic_a",
        "topic_b",
    ]
