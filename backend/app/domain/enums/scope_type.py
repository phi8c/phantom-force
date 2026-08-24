from enum import Enum

class ScopeType(
    str,
    Enum,
):
    SOURCE = "SOURCE"

    SITE = "SITE"

    FOLDER = "FOLDER"

    FILE = "FILE"