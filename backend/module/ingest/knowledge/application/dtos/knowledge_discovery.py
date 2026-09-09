from dataclasses import dataclass
from dataclasses import field
from typing import Any
from uuid import UUID


@dataclass(frozen=True)
class KnowledgeDiscoverySeed:
    seed_id: str
    object_code: str | None = None
    identifier_code: str | None = None
    information_type_code: str | None = None
    topic_codes: list[str] = field(default_factory=list)
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


@dataclass(frozen=True)
class KnowledgeDiscoveredSeed:
    seed_id: str
    matched_entry_points: KnowledgeMatchedEntryPoints
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
    seeds: list[KnowledgeDiscoverySeed] = field(default_factory=list)


@dataclass(frozen=True)
class KnowledgeDiscoveryResult:
    seeds: list[KnowledgeDiscoveredSeed] = field(default_factory=list)


@dataclass(frozen=True)
class KnowledgeRetrievalSelection:
    seed_id: str
    information_type_codes: list[str] = field(default_factory=list)
    topic_codes: list[str] = field(default_factory=list)
    field_codes: list[str] = field(default_factory=list)
    constraints: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class KnowledgeRetrievalRequest:
    knowledge_space_id: UUID
    discovered_seed: KnowledgeDiscoveredSeed
    selection: KnowledgeRetrievalSelection
