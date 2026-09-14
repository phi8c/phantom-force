from dataclasses import dataclass

from module.enterprise.application.enums import EnterpriseStatus


@dataclass(frozen=True)
class CreateEnterpriseRequest:
    code: str
    name: str
    description: str | None = None
    status: EnterpriseStatus = EnterpriseStatus.ACTIVE
