from __future__ import annotations

from pathlib import Path

from module.ingest.extraction.domain.contracts.extraction_engine import (
    ExtractionEngine,
    ExtractionResult,
)

from .engine import UnstructuredEngine


class UnstructuredExtractor(ExtractionEngine):
    def __init__(self, engine: UnstructuredEngine | None = None) -> None:
        self._engine = engine or UnstructuredEngine()

    async def extract(self, file_path: Path) -> ExtractionResult:
        document = self._engine.parse(file_path)
        return ExtractionResult(content=document.model_dump())
