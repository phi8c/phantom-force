from module.ingest.extraction.domain.contracts.extraction_engine import (
    ExtractionEngine,
    ExtractionResult,
)
from module.ingest.extraction.engine.docling.engine import (
    DocumentEngine,
)


class DoclingExtractor(
    ExtractionEngine,
):

    def __init__(self):
        self.engine = DocumentEngine()

    async def extract(
        self,
        file_path,
    ) -> ExtractionResult:
        document = self.engine.parse(
            file_path
        )

        return ExtractionResult(
            content=document.model_dump(),
        )
