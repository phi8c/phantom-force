from enum import Enum

class UserStatus(str, Enum):
    ACTIVE = "active"

    DISABLED = "disabled"

    PENDING_VERIFICATION = "pending_verification"