# app/utils/document_engine/models/section.py
from pydantic import BaseModel, Field
from typing import List, Optional

class BBox(BaseModel):
    l: float
    t: float
    r: float
    b: float

class TableModel(BaseModel):
    content: str  # Chứa Markdown hoặc HTML table
    page_no: Optional[int] = None

class ImageModel(BaseModel):
    image_base64: Optional[str] = None
    caption: Optional[str] = None
    page_no: Optional[int] = None

class SectionModel(BaseModel):

    id: str

    title: str

    level: int

    content: str = ""

    aggregated_content: str = ""

    token_count: int = 0

    aggregated_token_count: int = 0

    page_no: Optional[int] = None

    bbox: Optional[BBox] = None

    tables: List[TableModel] = (
        Field(default_factory=list)
    )

    images: List[ImageModel] = (
        Field(default_factory=list)
    )

    children: List["SectionModel"] = (
        Field(default_factory=list)
    )

# Yêu cầu của Pydantic khi dùng Recursive Model
SectionModel.model_rebuild()

class DocumentModel(BaseModel):
    title: str
    sections: List[SectionModel] = Field(default_factory=list)