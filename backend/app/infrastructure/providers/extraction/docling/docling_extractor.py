from app.domain.ports.extraction.document_extractor import (
    DocumentExtractor,
)

from app.infrastructure.providers.extraction.docling.engine import (
    DocumentEngine,
)


class DoclingExtractor(
    DocumentExtractor
):

    def __init__(self):
        self.engine = DocumentEngine()

    async def extract(
        self,
        file_path: str,
    ):
        return self.engine.parse(
            file_path
        )