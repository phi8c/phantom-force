from abc import ABC
from abc import abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ExtractionResult:
    content: dict[str, Any]
    content_type: str = "application/json"
    # Optional disk-backed JSON body. First line is a replaceable root header;
    # the rest contains streamed arrays. content holds that header only.
    content_file: Path | None = None


class ExtractionEngine(ABC):

    @abstractmethod
    async def extract(
        self,
        file_path: Path,
    ) -> ExtractionResult:
        pass
