from datetime import datetime
from uuid import UUID


class TableAsset:

    def __init__(
        self,
        document_id: UUID,
        sheet_name: str,
        schema_json: dict,
        storage_path: str,
    ):
        self.id: UUID | None = None

        self.document_id = document_id

        self.sheet_name = sheet_name

        self.description: str | None = None

        self.row_count: int | None = None

        self.schema_json = schema_json

        self.storage_path = storage_path

        self.created_at: datetime | None = None

    def set_id(
        self,
        value: UUID,
    ):
        self.id = value