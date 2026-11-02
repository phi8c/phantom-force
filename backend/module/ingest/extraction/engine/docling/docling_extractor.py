from pathlib import Path
import asyncio

from module.ingest.extraction.domain.contracts.extraction_engine import ExtractionEngine, ExtractionResult
from module.ingest.extraction.infrastructure.normalization.document_builder import serialize_document
from module.ingest.extraction.infrastructure.normalization.native_docx import NativeDocxReader
from module.ingest.extraction.infrastructure.normalization.provider_documents import normalize_docling
from module.ingest.extraction.infrastructure.normalization.runtime import package_version


class DoclingExtractor(ExtractionEngine):
    async def extract(self, file_path: Path) -> ExtractionResult:
        return await asyncio.to_thread(self._extract, Path(file_path))

    def _extract(self, path: Path) -> ExtractionResult:
        if path.suffix.lower() == '.docx':
            document = NativeDocxReader().read(path)
        elif path.suffix.lower() == '.pdf':
            from module.ingest.extraction.engine.docling.providers.docling_provider import DoclingProvider
            document = normalize_docling(DoclingProvider().parse(str(path)),
                                         document_id=path.stem, version=package_version('docling'))
        else:
            raise ValueError(f'Unsupported extraction suffix: {path.suffix}')
        return ExtractionResult(content=serialize_document(document))
