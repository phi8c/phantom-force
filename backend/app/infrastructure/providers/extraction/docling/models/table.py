from pydantic import BaseModel
from typing import Any


class TableBlock(BaseModel):
    id: str

    caption: str | None = None

    page_no: int | None = None

    rows: list[dict[str, Any]]