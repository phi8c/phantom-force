import asyncio
from collections.abc import AsyncIterator
import json

from module.ingest.extraction.domain.contracts.extraction_engine import ExtractionResult


async def extraction_output_stream(result: ExtractionResult) -> AsyncIterator[bytes]:
    if result.content_file is None:
        for chunk in json.JSONEncoder(ensure_ascii=False).iterencode(result.content):
            yield chunk.encode('utf-8')
        return
    with result.content_file.open('rb') as source:
        source.readline()
        yield (json.dumps(result.content, ensure_ascii=False)[:-1] + ',\n').encode('utf-8')
        while True:
            block = source.read(64 * 1024)
            if not block:
                break
            yield block
            await asyncio.sleep(0)
