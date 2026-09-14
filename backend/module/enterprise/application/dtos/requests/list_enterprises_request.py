from dataclasses import dataclass


@dataclass(frozen=True)
class ListEnterprisesRequest:
    limit: int = 20
    cursor: str | None = None
