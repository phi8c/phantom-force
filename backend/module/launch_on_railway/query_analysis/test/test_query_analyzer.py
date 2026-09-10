from module.launch_on_railway.query_analysis.application.services.query_analyzer import (
    MAX_DOCUMENT_TYPE_SEEDS,
    MAX_INFORMATION_FIELD_SEEDS,
    MAX_INFORMATION_TYPE_SEEDS,
    MAX_KNOWLEDGE_REQUESTS,
    MAX_OBJECT_SEEDS,
    MAX_TOPIC_SEEDS,
    QueryAnalyzer,
)


def test_parse_knowledge_requests_enforces_limits_and_dedupes():
    parsed = QueryAnalyzer._parse_knowledge_requests(
        [
            {
                "need": " compare browsers ",
                "document_type_seeds": [
                    "manual",
                    "manual",
                    "policy",
                    "reference",
                    "extra",
                ],
                "topic_seeds": [
                    "cache_policy",
                    None,
                    "cache_policy",
                    "browser_cache",
                    "http_cache",
                    "edge_cache",
                    "overflow",
                ],
                "object_seeds": [
                    "chrome",
                    "edge",
                    "chrome",
                    "browser",
                    "chromium",
                    "overflow",
                ],
                "information_type_seeds": [
                    "policy",
                    "rule",
                    "policy",
                    "configuration",
                    "behavior",
                    "overflow",
                ],
                "information_field_seeds": [
                    "ttl",
                    "cache_control",
                    "ttl",
                    "etag",
                    "expires",
                    "overflow",
                ],
                "constraints": "invalid",
                "confidence": "0.82",
            }
        ]
    )

    assert len(parsed) == 1
    request = parsed[0]
    assert request.need == "compare browsers"
    assert request.document_type_seeds == [
        "manual",
        "policy",
        "reference",
    ][:MAX_DOCUMENT_TYPE_SEEDS]
    assert request.topic_seeds == [
        "cache_policy",
        "browser_cache",
        "http_cache",
        "edge_cache",
    ][:MAX_TOPIC_SEEDS]
    assert request.object_seeds == [
        "chrome",
        "edge",
        "browser",
        "chromium",
    ][:MAX_OBJECT_SEEDS]
    assert request.information_type_seeds == [
        "policy",
        "rule",
        "configuration",
        "behavior",
    ][:MAX_INFORMATION_TYPE_SEEDS]
    assert request.information_field_seeds == [
        "ttl",
        "cache_control",
        "etag",
        "expires",
    ][:MAX_INFORMATION_FIELD_SEEDS]
    assert request.constraints == {}
    assert request.confidence == 0.82


def test_parse_simple_vietnamese_question_shape():
    parsed = QueryAnalyzer._parse_knowledge_requests(
        [
            {
                "need": "Tìm điều kiện nghiệm thu",
                "topic_seeds": [
                    "nghiệm thu",
                ],
                "information_type_seeds": [
                    "điều kiện",
                ],
                "confidence": 0.7,
            }
        ]
    )

    assert len(parsed) == 1
    assert parsed[0].need == "Tìm điều kiện nghiệm thu"
    assert parsed[0].topic_seeds == [
        "nghiệm thu",
    ]
    assert parsed[0].information_type_seeds == [
        "điều kiện",
    ]
    assert parsed[0].confidence == 0.7


def test_parse_knowledge_requests_keeps_valid_need_without_seeds():
    parsed = QueryAnalyzer._parse_knowledge_requests(
        [
            {
                "need": "Summarize deployment requirements",
                "constraints": {
                    "scope": "broad",
                },
                "confidence": "not-a-number",
            }
        ]
    )

    assert len(parsed) == 1
    assert parsed[0].need == "Summarize deployment requirements"
    assert parsed[0].topic_seeds == []
    assert parsed[0].constraints == {
        "scope": "broad",
    }
    assert parsed[0].confidence is None


def test_parse_knowledge_requests_discards_empty_need():
    parsed = QueryAnalyzer._parse_knowledge_requests(
        [
            {
                "need": "",
                "topic_seeds": [
                    "acceptance",
                ],
            },
            {
                "topic_seeds": [
                    "deployment",
                ],
            },
        ]
    )

    assert parsed == []


def test_parse_knowledge_requests_ignores_legacy_flat_seeds_shape():
    parsed = QueryAnalyzer._parse_knowledge_requests(
        [
            {
                "object_code": "chrome",
                "topic_codes": [
                    "cache_policy",
                ],
            }
        ]
    )

    assert parsed == []


def test_parse_knowledge_requests_limits_request_count():
    parsed = QueryAnalyzer._parse_knowledge_requests(
        [
            {
                "need": f"Need {index}",
            }
            for index in range(MAX_KNOWLEDGE_REQUESTS + 2)
        ]
    )

    assert len(parsed) == MAX_KNOWLEDGE_REQUESTS
    assert parsed[-1].need == f"Need {MAX_KNOWLEDGE_REQUESTS - 1}"


def test_confidence_validation_only_accepts_zero_to_one():
    parsed = QueryAnalyzer._parse_knowledge_requests(
        [
            {
                "need": "Below lower bound",
                "confidence": -1,
            },
            {
                "need": "Above upper bound",
                "confidence": 2,
            },
            {
                "need": "Invalid confidence",
                "confidence": "invalid",
            },
            {
                "need": "Valid confidence",
                "confidence": 0.7,
            },
        ]
    )

    assert [
        item.confidence
        for item in parsed
    ] == [
        None,
        None,
        None,
        0.7,
    ]
