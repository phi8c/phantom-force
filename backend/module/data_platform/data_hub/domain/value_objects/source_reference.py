from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping


@dataclass(frozen=True, slots=True)
class SourceReference:
    """
    Provider-neutral reference to a data source or source location.

    The reference must not depend on provider-specific concepts such as
    SharePoint site, drive, folder, S3 bucket, or Google Drive.
    """

    provider: str
    identifier: str
    metadata: Mapping[str, Any] = field(default_factory=dict)