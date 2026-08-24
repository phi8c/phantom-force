from enum import Enum
class TriggerType(
    str,
    Enum,
):
    MANUAL = "MANUAL"

    SCHEDULED_SCAN = "SCHEDULED_SCAN"

    LARGE_BUILD = "LARGE_BUILD"