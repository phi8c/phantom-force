from __future__ import annotations

from pydantic import BaseModel, Field


class BBox(BaseModel):
    l: float
    t: float
    r: float
    b: float


class TableModel(BaseModel):
    content: str
    page_no: int | None = None


class ImageModel(BaseModel):
    image_base64: str | None = None
    caption: str | None = None
    page_no: int | None = None


class SectionModel(BaseModel):
    id: str
    title: str
    level: int
    content: str = ""
    aggregated_content: str = ""
    token_count: int = 0
    aggregated_token_count: int = 0
    page_no: int | None = None
    bbox: BBox | None = None
    tables: list[TableModel] = Field(default_factory=list)
    images: list[ImageModel] = Field(default_factory=list)
    children: list[SectionModel] = Field(default_factory=list)


SectionModel.model_rebuild()
