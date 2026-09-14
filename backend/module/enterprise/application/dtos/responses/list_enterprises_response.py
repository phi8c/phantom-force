from dataclasses import dataclass

from module.enterprise.application.dtos.responses.enterprise_response import (
    EnterpriseResponse,
)


@dataclass(frozen=True)
class ListEnterprisesResponse:
    items: list[EnterpriseResponse]
    next_cursor: str | None
    has_more: bool
