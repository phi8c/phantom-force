from enum import Enum


class TaskType(
    str,
    Enum,
):
    DOWNLOAD = "DOWNLOAD"

    EXTRACT = "EXTRACT"

    CHUNK = "CHUNK"

    EMBED = "EMBED"

    CLASSIFY = "CLASSIFY"

    INDEX = "INDEX"