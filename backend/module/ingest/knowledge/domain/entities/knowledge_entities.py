from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID


@dataclass
class KnowledgeDocumentType:
    id: UUID | None
    knowledge_space_id: UUID
    code: str
    name: str | None
    description: str | None
    structuring_guidance: dict[str, Any] | None
    metadata: dict[str, Any] | None
    created_at: datetime | None
    updated_at: datetime | None


@dataclass
class KnowledgeObject:
    id: UUID | None
    knowledge_space_id: UUID
    object_code: str
    identifier_code: str | None
    object_name: str | None
    identifier_name: str | None
    description: str | None
    aliases: list[Any] | dict[str, Any] | None
    metadata: dict[str, Any] | None
    created_at: datetime | None
    updated_at: datetime | None


@dataclass
class KnowledgeInformationType:
    id: UUID | None
    knowledge_space_id: UUID
    code: str
    name: str | None
    description: str | None
    metadata: dict[str, Any] | None
    created_at: datetime | None
    updated_at: datetime | None


@dataclass
class KnowledgeInformationField:
    id: UUID | None
    knowledge_space_id: UUID
    code: str
    name: str | None
    description: str | None
    data_type: str | None
    unit_type: str | None
    metadata: dict[str, Any] | None
    created_at: datetime | None
    updated_at: datetime | None


@dataclass
class KnowledgeTopic:
    id: UUID | None
    knowledge_space_id: UUID
    code: str
    name: str | None
    description: str | None
    metadata: dict[str, Any] | None
    created_at: datetime | None
    updated_at: datetime | None


@dataclass
class KnowledgeInformation:
    id: UUID | None
    knowledge_space_id: UUID
    information_type_id: UUID | None
    summary: str
    data: dict[str, Any] | None
    object_refs: list[dict[str, Any]] | None
    topic_refs: list[dict[str, Any]] | None
    source_refs: list[dict[str, Any]] | None
    confidence: float | None
    raw_model_output: dict[str, Any] | None
    metadata: dict[str, Any] | None
    created_at: datetime | None
    updated_at: datetime | None


@dataclass
class KnowledgeInformationSearchRecord:
    information_id: UUID
    information_type_code: str | None
    summary: str
    data: dict[str, Any] | None
    object_refs: list[dict[str, Any]] | None
    topic_refs: list[dict[str, Any]] | None
    source_refs: list[dict[str, Any]] | None
    confidence: float | None


@dataclass
class KnowledgeObjectStructureRecord:
    object_code: str
    identifier_code: str | None
    name: str | None
    identifier_name: str | None
    description: str | None


@dataclass
class KnowledgeCodeStructureRecord:
    code: str
    name: str | None
    description: str | None
    data_type: str | None = None


@dataclass
class KnowledgeMatchedEntryPointsRecord:
    objects: list[KnowledgeObjectStructureRecord]
    information_types: list[KnowledgeCodeStructureRecord]
    topics: list[KnowledgeCodeStructureRecord]


@dataclass
class KnowledgeDiscoveredSeedRecord:
    seed_id: str
    matched_entry_points: KnowledgeMatchedEntryPointsRecord
    available_objects: list[KnowledgeObjectStructureRecord]
    available_information_types: list[KnowledgeCodeStructureRecord]
    available_topics: list[KnowledgeCodeStructureRecord]
    available_fields: list[KnowledgeCodeStructureRecord]
    constraints: dict[str, Any]
