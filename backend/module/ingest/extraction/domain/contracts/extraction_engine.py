from abc import ABC
from abc import abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ExtractionResult:
    content: dict[str, Any]
    content_type: str = "application/json"


class ExtractionEngine(ABC):

    @abstractmethod
    async def extract(
        self,
        file_path: Path,
    ) -> ExtractionResult:
        pass
