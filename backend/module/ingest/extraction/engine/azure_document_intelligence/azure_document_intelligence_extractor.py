import asyncio
from pathlib import Path

from module.ingest.extraction.domain.contracts.extraction_engine import ExtractionEngine, ExtractionResult
from module.ingest.extraction.infrastructure.normalization.native_docx import NativeDocxReader
from module.ingest.extraction.infrastructure.normalization.document_builder import serialize_document
from module.ingest.extraction.infrastructure.normalization.provider_documents import normalize_azure


class AzureDocumentIntelligenceExtractor(ExtractionEngine):
    def __init__(self, *, endpoint: str, key: str):
        if not endpoint or not key:
            raise ValueError('Azure Document Intelligence endpoint and key are required')
        self._endpoint = endpoint
        self._key = key

    async def extract(self, file_path: Path) -> ExtractionResult:
        path = Path(file_path)
        if path.suffix.lower() == '.docx':
            document = await asyncio.to_thread(NativeDocxReader().read, path)
        elif path.suffix.lower() == '.pdf':
            from azure.ai.documentintelligence.aio import DocumentIntelligenceClient
            from azure.core.credentials import AzureKeyCredential
            async with DocumentIntelligenceClient(self._endpoint, AzureKeyCredential(self._key)) as client:
                with path.open('rb') as source:
                    poller = await client.begin_analyze_document(model_id='prebuilt-layout', body=source)
                    result = await poller.result()
            document = normalize_azure(result, document_id=path.stem, title=path.stem, version='prebuilt-layout')
        else:
            raise ValueError(f'Unsupported extraction suffix: {path.suffix}')
        return ExtractionResult(content=serialize_document(document))
