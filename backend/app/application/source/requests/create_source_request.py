from dataclasses import dataclass


@dataclass
class CreateSourceRequest:
    name: str
    source_type: str
    site_id: str
    drive_id: str | None