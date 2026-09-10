import json

from module.ingest.knowledge.application.dtos import (
    KnowledgeCodeStructure,
    KnowledgeDiscoveredSeed,
    KnowledgeMatchedEntryPoints,
    KnowledgeObjectStructure,
)
from module.launch_on_railway.knowledge_selection.application.services.knowledge_selector import (
    KnowledgeSelector,
)


def test_build_user_prompt_uses_knowledge_candidates_contract():
    candidate = KnowledgeDiscoveredSeed(
        seed_id="knowledge_1",
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
    candidate = KnowledgeDiscoveredSeed(
        seed_id="knowledge_1",
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
    assert selections[0].seed_id == "knowledge_1"
    assert selections[0].information_type_codes == [
        "policy",
    ]
    assert selections[0].topic_codes == [
        "cache_policy",
    ]
    assert selections[0].field_codes == [
        "ttl",
    ]
