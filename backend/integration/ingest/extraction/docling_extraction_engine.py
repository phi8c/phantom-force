from pathlib import Path

from module.ingest.extraction.domain.contracts.extraction_engine import (
    ExtractionEngine,
    ExtractionResult,
)
from module.ingest.extraction.engine.docling.docling_extractor import (
    DoclingExtractor,
)


class DoclingExtractionEngine(
    ExtractionEngine,
):

    def __init__(
        self,
        extractor: DoclingExtractor | None = None,
    ):
        self._extractor = (
            extractor
            or DoclingExtractor()
        )

    async def extract(
        self,
        file_path: Path,
    ) -> ExtractionResult:
        return await self._extractor.extract(
            file_path,
        )
