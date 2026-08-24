from enum import Enum


class SourceType(
    str,
    Enum,
):
    SHAREPOINT = "SHAREPOINT"

    CONFLUENCE = "CONFLUENCE"

    GOOGLE_DRIVE = "GOOGLE_DRIVE"