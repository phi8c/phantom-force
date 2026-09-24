from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


@dataclass(frozen=True, slots=True)
class DropboxConfiguration:
    app_key: str
    app_secret: str
    refresh_token: str
    root_path: str = ""

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any] | None) -> "DropboxConfiguration":
        configuration = value or {}
        credentials: dict[str, str] = {}
        for field_name in ("app_key", "app_secret", "refresh_token"):
            field_value = configuration.get(field_name)
            if not isinstance(field_value, str) or not field_value.strip():
                raise ValueError(f"Dropbox configuration requires non-empty '{field_name}'.")
            credentials[field_name] = field_value.strip()

        root_path = configuration.get("root_path", "")
        if not isinstance(root_path, str):
            raise ValueError("Dropbox configuration 'root_path' must be a string.")
        return cls(root_path=normalize_dropbox_path(root_path), **credentials)

    def resolve_path(self, path: str | None) -> str:
        requested = normalize_dropbox_path(path or self.root_path)
        if not self.root_path:
            return requested
        root_lower = self.root_path.lower()
        requested_lower = requested.lower()
        if requested_lower != root_lower and not requested_lower.startswith(root_lower + "/"):
            raise ValueError(
                f"Dropbox path '{requested or '/'}' is outside configured root '{self.root_path}'."
            )
        return requested


def normalize_dropbox_path(path: str) -> str:
    normalized = path.strip().replace("\\", "/")
    if normalized in {"", "/"}:
        return ""
    return "/" + normalized.strip("/")
