from pydantic import BaseModel


class ImageBlock(BaseModel):
    id: str

    caption: str | None = None

    page_no: int | None = None

    path: str | None = None