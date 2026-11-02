import asyncio
from pathlib import Path

from module.ingest.extraction.domain.contracts.extraction_engine import ExtractionEngine, ExtractionResult
from module.ingest.extraction.infrastructure.normalization.native_docx import NativeDocxReader
from module.ingest.extraction.infrastructure.normalization.document_builder import serialize_document
from module.ingest.extraction.infrastructure.normalization.unstructured_document import normalize_unstructured
from module.ingest.extraction.infrastructure.normalization.runtime import package_version
from .providers.unstructured_provider import UnstructuredProvider


class UnstructuredExtractor(ExtractionEngine):
    def __init__(self, provider=None, pdf_strategy='hi_res'):
        # Layout inference is needed for table grids; no image assets are emitted.
        self._provider = provider or UnstructuredProvider(pdf_strategy=pdf_strategy)

    async def extract(self, file_path: Path) -> ExtractionResult:
        return await asyncio.to_thread(self._extract, Path(file_path))

    def _extract(self, path):
        if path.suffix.lower() == '.docx':
            document = NativeDocxReader().read(path)
        elif path.suffix.lower() == '.pdf':
            document = normalize_unstructured(self._provider.partition(path),
                document_id=path.stem, title=path.stem, version=package_version('unstructured'))
        else:
            raise ValueError(f'Unsupported extraction suffix: {path.suffix}')
        return ExtractionResult(content=serialize_document(document))
