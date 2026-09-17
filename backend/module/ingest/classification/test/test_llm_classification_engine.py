from uuid import uuid4

import pytest

from module.ingest.classification.infrastructure.engine.llm_classification_engine import (
    LLMClassificationEngine,
)


def test_normalizes_declared_object_references():
    response = {
        "objects": [
            {"object_code": "market", "identifier_code": "hanoi_market"},
            {"object_code": "policy"},
        ],
        "information": [
            {
                "object_refs": [
                    {"identifier_code": "hanoi_market"},
                    {"object_code": "policy"},
                    {"object_code": "market"},
                ]
            },
            {"object_refs": ["market"]},
        ],
    }

    LLMClassificationEngine._normalize_object_refs(response, uuid4())

    assert response["information"][0]["object_refs"] == [
        "hanoi_market",
        "policy",
        "hanoi_market",
    ]
    assert response["information"][1]["object_refs"] == ["hanoi_market"]


@pytest.mark.parametrize(
    "ref",
    [
        {"identifier_code": "missing"},
        {"name": "Hanoi market"},
        123,
    ],
)
def test_rejects_ambiguous_or_undeclared_object_references(ref):
    response = {
        "objects": [
            {"object_code": "market", "identifier_code": "hanoi_market"}
        ],
        "information": [{"object_refs": [ref]}],
    }

    with pytest.raises(ValueError, match="invalid or undeclared object"):
        LLMClassificationEngine._normalize_object_refs(response, uuid4())


def test_rejects_object_code_shared_by_multiple_identifiers():
    response = {
        "objects": [
            {"object_code": "market", "identifier_code": "hanoi_market"},
            {"object_code": "market", "identifier_code": "saigon_market"},
        ],
        "information": [{"object_refs": ["market"]}],
    }

    with pytest.raises(ValueError, match="invalid or undeclared object"):
        LLMClassificationEngine._normalize_object_refs(response, uuid4())
