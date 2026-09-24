from __future__ import annotations

from pathlib import Path
from typing import Any, Protocol

from .models import SectionModel


class PartitionProvider(Protocol):
    def partition(self, file_path: Path) -> list[Any]: ...


class ElementSerializer(Protocol):
    def serialize(self, element: Any) -> dict[str, Any]: ...


class SectionProcessor(Protocol):
    @property
    def warnings(self) -> list[str]: ...

    def process(self, elements: list[Any]) -> list[SectionModel]: ...
