from pydantic import BaseModel, Field

from .section import Section


class Document(BaseModel):
    title: str | None = None

    sections: list[Section] = Field(
        default_factory=list
    )