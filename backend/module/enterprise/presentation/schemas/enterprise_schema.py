from datetime import datetime
from uuid import UUID

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field

from module.enterprise.application.enums import EnterpriseStatus


class CreateEnterpriseSchema(BaseModel):
    code: str = Field(
        min_length=1,
        max_length=100,
    )
    name: str = Field(
        min_length=1,
        max_length=255,
    )
    description: str | None = None
    status: EnterpriseStatus = EnterpriseStatus.ACTIVE


class UpdateEnterpriseSchema(BaseModel):
    code: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
    )
    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=255,
    )
    description: str | None = None
    status: EnterpriseStatus | None = None


class EnterpriseSchema(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
    )

    id: UUID
    code: str
    name: str
    description: str | None
    status: str
    created_at: datetime | None
    updated_at: datetime | None


class EnterpriseListSchema(BaseModel):
    items: list[EnterpriseSchema]
    next_cursor: str | None
    has_more: bool


class EnterpriseOptionSchema(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
    )

    id: UUID
    code: str
    name: str
