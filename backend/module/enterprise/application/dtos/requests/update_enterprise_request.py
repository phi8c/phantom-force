from dataclasses import dataclass

from module.enterprise.application.enums import EnterpriseStatus


@dataclass(frozen=True)
class UpdateEnterpriseRequest:
    code: str | None = None
    name: str | None = None
    description: str | None = None
    description_provided: bool = False
    status: EnterpriseStatus | None = None
