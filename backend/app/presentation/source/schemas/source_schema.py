from pydantic import BaseModel


class CreateSourceSchema(
    BaseModel,
):
    name: str

    source_type: str

    site_id: str

    drive_id: str | None = None