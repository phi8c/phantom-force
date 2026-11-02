from contextlib import aclosing
from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path
from time import perf_counter
import tracemalloc


@dataclass(frozen=True)
class VerificationReport:
    source_sha256: str
    source_bytes: int
    extracted_bytes: int
    chunk_count: int
    chunk_content_characters: int
    chunk_sha256: str
    extraction_seconds: float
    chunking_seconds: float
    parent_python_peak_bytes: int
    coverage_validation: str = 'passed_by_chunker'

    def as_dict(self):
        return asdict(self)


def file_digest(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


class VerificationRunner:
    """Measure injected extraction/chunk streams without retaining document content.

    The chunk adapter must exhaust canonical coverage validation before finishing.
    No providers, storage SDKs, ORM or module implementations are imported here.
    """

    def __init__(self, *, extract, chunks):
        self.extract = extract
        self.chunks = chunks

    async def run(self, source: Path):
        source = source.resolve(strict=True)
        identity = file_digest(source)
        owns_trace = not tracemalloc.is_tracing()
        if owns_trace:
            tracemalloc.start()
        try:
            started = perf_counter()
            extracted = await self.extract(source)
            extraction_seconds = perf_counter() - started
            started = perf_counter()
            count = characters = 0
            digest = hashlib.sha256()
            async with aclosing(self.chunks(extracted)) as stream:
                async for chunk in stream:
                    if chunk.index != count or not chunk.content.strip():
                        raise ValueError('Verification encountered invalid chunk order or empty content')
                    value = json.dumps({'index': chunk.index, 'title': chunk.title,
                        'content': chunk.content, 'metadata': chunk.metadata},
                        ensure_ascii=False, sort_keys=True).encode('utf-8')
                    digest.update(len(value).to_bytes(8, 'big'))
                    digest.update(value)
                    count += 1
                    characters += len(chunk.content)
            if not count:
                raise ValueError('Verification produced zero chunks')
            if file_digest(source) != identity:
                raise ValueError('Source changed during verification')
            return VerificationReport(identity, source.stat().st_size, extracted.stat().st_size,
                count, characters, digest.hexdigest(), extraction_seconds, perf_counter() - started,
                tracemalloc.get_traced_memory()[1])
        finally:
            if owns_trace:
                tracemalloc.stop()
