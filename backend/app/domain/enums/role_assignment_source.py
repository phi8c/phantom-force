from enum import Enum


class RoleAssignmentSource(str, Enum):
    MANUAL = "manual"
    ENTRA_SYNC = "entra_sync"