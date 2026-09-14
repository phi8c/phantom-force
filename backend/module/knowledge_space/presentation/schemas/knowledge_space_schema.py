from datetime import datetime
from uuid import UUID

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field


class CreateKnowledgeSpaceSchema(BaseModel):
    enterprise_id: UUID
    name: str = Field(
        min_length=1,
        max_length=255,
    )
    code: str = Field(
        min_length=1,
        max_length=100,
    )
    description: str | None = None
    configuration: dict = Field(
        default_factory=dict,
    )


class KnowledgeSpaceSchema(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
    )

    id: UUID
    enterprise_id: UUID
    name: str
    code: str
    description: str | None
    status: str
    configuration: dict
    created_at: datetime | None
    updated_at: datetime | None


class KnowledgeSpaceListItemSchema(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
    )

    id: UUID
    enterprise_id: UUID
    enterprise_name: str
    name: str
    code: str
    description: str | None
    status: str
    created_at: datetime | None


class KnowledgeSpaceListSchema(BaseModel):
    items: list[KnowledgeSpaceListItemSchema]
    page: int
    page_size: int
    total: int


class SaveDataHubConfigSchema(BaseModel):
    data_hub_provider_id: UUID
    configuration: dict = Field(
        default_factory=dict,
    )
    enabled: bool = True


class SaveEmbeddingConfigSchema(BaseModel):
    embedding_model_id: UUID
    configuration: dict = Field(
        default_factory=dict,
    )
    enabled: bool = True


class KnowledgeSpaceDataHubSchema(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
    )

    id: UUID
    knowledge_space_id: UUID
    data_hub_provider_id: UUID
    configuration: dict
    enabled: bool
    created_at: datetime | None
    updated_at: datetime | None


class KnowledgeSpaceEmbeddingSchema(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
    )

    id: UUID
    knowledge_space_id: UUID
    embedding_model_id: UUID
    configuration: dict
    enabled: bool
    created_at: datetime | None
    updated_at: datetime | None


class KnowledgeSpaceDataHubEnvelopeSchema(BaseModel):
    configured: bool
    data: KnowledgeSpaceDataHubSchema | None


class KnowledgeSpaceEmbeddingEnvelopeSchema(BaseModel):
    configured: bool
    data: KnowledgeSpaceEmbeddingSchema | None
