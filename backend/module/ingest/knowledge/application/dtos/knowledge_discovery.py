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

    @property
    def seed_id(self) -> str:
        return self.request_id

    @property
    def object_code(self) -> str | None:
        return self.object_seeds[0] if self.object_seeds else None

    @property
    def identifier_code(self) -> str | None:
        return (
            self.identifier_seeds[0]
            if self.identifier_seeds
            else None
        )

    @property
    def information_type_code(self) -> str | None:
        return (
            self.information_type_seeds[0]
            if self.information_type_seeds
            else None
        )

    @property
    def topic_codes(self) -> list[str]:
        return self.topic_seeds


@dataclass(frozen=True)
class KnowledgeDiscoverySeed(KnowledgeDiscoveryRequestItem):
    def __init__(
        self,
        seed_id: str,
        object_code: str | None = None,
        identifier_code: str | None = None,
        information_type_code: str | None = None,
        topic_codes: list[str] | None = None,
        constraints: dict[str, Any] | None = None,
    ):
        object.__setattr__(self, "request_id", seed_id)
        object.__setattr__(self, "need", "")
        object.__setattr__(self, "document_type_seeds", [])
        object.__setattr__(self, "head_seeds", [])
        object.__setattr__(
            self,
            "topic_seeds",
            list(topic_codes or []),
        )
        object.__setattr__(
            self,
            "object_seeds",
            [object_code] if object_code is not None else [],
        )
        object.__setattr__(
            self,
            "identifier_seeds",
            [identifier_code] if identifier_code is not None else [],
        )
        object.__setattr__(
            self,
            "information_type_seeds",
            (
                [information_type_code]
                if information_type_code is not None
                else []
            ),
        )
        object.__setattr__(self, "information_field_seeds", [])
        object.__setattr__(self, "constraints", dict(constraints or {}))


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
class KnowledgeDiscoveredSeed:
    seed_id: str
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
    seeds: list[KnowledgeDiscoverySeed] = field(default_factory=list)

    def __post_init__(self):
        if self.items:
            return
        if self.seeds:
            object.__setattr__(
                self,
                "items",
                list(self.seeds),
            )


@dataclass(frozen=True)
class KnowledgeDiscoveryResult:
    seeds: list[KnowledgeDiscoveredSeed] = field(default_factory=list)

    @property
    def requests(self) -> list[KnowledgeDiscoveredSeed]:
        return self.seeds


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
