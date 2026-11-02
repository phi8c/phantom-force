"""Internal subprocess entry point. Secrets are never written to the request."""
import asyncio
import json
from pathlib import Path
import sys

from .checkpoints import atomic_json


async def main():
    request = json.loads(sys.stdin.buffer.read())
    engine_name = request['engine']
    if engine_name == 'docling':
        from module.ingest.extraction.engine.docling.docling_extractor import DoclingExtractor
        engine = DoclingExtractor()
    elif engine_name == 'unstructured':
        from module.ingest.extraction.engine.unstructured.unstructured_extractor import UnstructuredExtractor
        engine = UnstructuredExtractor()
    elif engine_name == 'azure_document_intelligence':
        from module.ingest.extraction.engine.azure_document_intelligence.azure_document_intelligence_extractor import AzureDocumentIntelligenceExtractor
        from shared.config.settings import settings
        engine = AzureDocumentIntelligenceExtractor(endpoint=settings.AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT,
                                                   key=settings.AZURE_DOCUMENT_INTELLIGENCE_KEY)
    else:
        raise ValueError('Unknown extraction engine')
    try:
        result = await engine.extract(Path(request['source']))
        payload = result.content
    except ValueError as error:
        if str(error) not in {'Extraction contains no content blocks', 'Extraction contains no readable text'}:
            raise
        payload = {'schema_version': 2, 'empty_part': True, 'blocks': [], 'tables': [], 'sections': [],
                   'extraction': {'warnings': ['No readable text/table content in this part']}}
    atomic_json(Path(request['destination']), payload)


if __name__ == '__main__':
    # Read once so failure metadata can be saved without exposing credentials.
    import io
    raw = sys.stdin.buffer.read()
    request = json.loads(raw)
    error_path = Path(request['destination']).with_suffix('.error.json')
    error_path.unlink(missing_ok=True)
    sys.stdin = io.TextIOWrapper(io.BytesIO(raw), encoding='utf-8')
    try:
        asyncio.run(main())
    except Exception as error:
        status = getattr(error, 'status_code', None)
        resource_error = isinstance(error, (MemoryError, TimeoutError))
        transient = resource_error or isinstance(error, (ConnectionError, OSError)) or status in {408, 429, 500, 502, 503, 504}
        atomic_json(error_path, {'message': f'{type(error).__name__}: part extraction failed; see part log',
                                'can_split': resource_error, 'retryable': transient})
        raise
