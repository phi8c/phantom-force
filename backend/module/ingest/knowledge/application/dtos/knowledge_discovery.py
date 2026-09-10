from dataclasses import dataclass
from dataclasses import field
from typing import Any
from uuid import UUID


@dataclass(frozen=True)
class KnowledgeDiscoveryRequestItem:
    request_id: str
    need: str = ""
    document_type_seeds: list[str] = field(default_factory=list)
    head_seeds: list[str] = field(default_factory=list)
    topic_seeds: list[str] = field(default_factory=list)
    object_seeds: list[str] = field(default_factory=list)
    identifier_seeds: list[str] = field(default_factory=list)
    information_type_seeds: list[str] = field(default_factory=list)
    information_field_seeds: list[str] = field(default_factory=list)
    constraints: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class KnowledgeObjectStructure:
    object_code: str
    identifier_code: str | None = None
    name: str | None = None
    identifier_name: str | None = None
    description: str | None = None


@dataclass(frozen=True)
class KnowledgeCodeStructure:
    code: str
    name: str | None = None
    description: str | None = None
    data_type: str | None = None


@dataclass(frozen=True)
class KnowledgeMatchedEntryPoints:
    objects: list[KnowledgeObjectStructure] = field(
        default_factory=list,
    )
    information_types: list[KnowledgeCodeStructure] = field(
        default_factory=list,
    )
    topics: list[KnowledgeCodeStructure] = field(
        default_factory=list,
    )
    fields: list[KnowledgeCodeStructure] = field(
        default_factory=list,
    )


@dataclass(frozen=True)
class KnowledgeDiscoveredRequest:
    request_id: str
    matched_entry_points: KnowledgeMatchedEntryPoints
    need: str = ""
    original_seeds: dict[str, list[str]] = field(default_factory=dict)
    available_objects: list[KnowledgeObjectStructure] = field(
        default_factory=list,
    )
    available_information_types: list[KnowledgeCodeStructure] = field(
        default_factory=list,
    )
    available_topics: list[KnowledgeCodeStructure] = field(
        default_factory=list,
    )
    available_fields: list[KnowledgeCodeStructure] = field(
        default_factory=list,
    )
    constraints: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class KnowledgeDiscoveryRequest:
    knowledge_space_id: UUID
    items: list[KnowledgeDiscoveryRequestItem] = field(default_factory=list)


@dataclass(frozen=True)
class KnowledgeDiscoveryResult:
    requests: list[KnowledgeDiscoveredRequest] = field(default_factory=list)


@dataclass(frozen=True)
class KnowledgeRetrievalSelection:
    request_id: str
    information_type_codes: list[str] = field(default_factory=list)
    topic_codes: list[str] = field(default_factory=list)
    field_codes: list[str] = field(default_factory=list)
    constraints: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class KnowledgeRetrievalRequest:
    knowledge_space_id: UUID
    discovered_request: KnowledgeDiscoveredRequest
    selection: KnowledgeRetrievalSelection
