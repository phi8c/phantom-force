from enum import Enum


class RoleSource(str, Enum):
    SYSTEM = "system"
    ENTRA_SYNC = "entra_sync"