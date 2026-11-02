"""Composition root for the opt-in local ingestion verification CLI."""
from contextlib import aclosing
from uuid import NAMESPACE_URL, uuid5

from module.ingest.extraction.infrastructure.multipart.engine import MultipartExtractionEngine
from module.ingest.chunking.infrastructure.engine.streaming_chunking_engine import StreamingChunkingEngine
from module.ingest.chunking.domain.contracts.chunking_engine import ExtractedDocument
from module.ingest.chunking.application.services.async_chunks import iterate_chunks
from module.ingest.chunking.application.services.chunk_budget import ChunkBudget
from tools.ingestion_verification.runner import VerificationRunner


def create_ingestion_verifier(*, engine, cache_root, pages_per_part=20, blocks_per_part=200,
                              max_chunk_tokens=800):
    extraction = MultipartExtractionEngine(engine, {'extraction_runtime': {
        'pdf_pages_per_part': pages_per_part, 'docx_blocks_per_part': blocks_per_part,
    }}, cache_root=cache_root)
    chunker = StreamingChunkingEngine(max_chunk_tokens=max_chunk_tokens)
    budget = ChunkBudget(max_chunk_tokens)

    async def extract(source):
        if source.suffix.lower() == '.json':
            return source
        result = await extraction.extract(source)
        if result.content_file is None:
            raise ValueError('Verification requires the multipart extraction artifact')
        return result.content_file

    async def chunks(path):
        document = ExtractedDocument(uuid5(NAMESPACE_URL, str(path.resolve())), path)
        async with chunker.open_chunks(document) as values:
            async with aclosing(iterate_chunks(values)) as stream:
                async for chunk in stream:
                    if not budget.fits(chunk.content, chunk.metadata):
                        raise ValueError('Chunk exceeds its configured content/provenance budget')
                    yield chunk

    return VerificationRunner(extract=extract, chunks=chunks)
