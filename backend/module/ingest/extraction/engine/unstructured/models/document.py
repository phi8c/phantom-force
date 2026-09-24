from pydantic import BaseModel, Field

from .section import SectionModel


class DocumentModel(BaseModel):
    """Unstructured output contract, compatible with Docling's JSON shape."""

    title: str
    sections: list[SectionModel] = Field(default_factory=list)
