from dataclasses import dataclass


@dataclass
class RolePermission:

    role_id: str

    permission_id: str