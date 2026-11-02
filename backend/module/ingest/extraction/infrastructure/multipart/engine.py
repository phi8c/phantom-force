import asyncio
from dataclasses import replace
import hashlib
import json
import os
from pathlib import Path

from shared.ingestion.parts import ExtractionManifest, ExtractionPart, PartStatus
from module.ingest.extraction.domain.contracts.extraction_engine import ExtractionEngine, ExtractionResult
from module.ingest.extraction.domain.contracts.extraction_parts import PartExecutor
from module.ingest.extraction.infrastructure.normalization.document_codec import decode_document
from module.ingest.extraction.infrastructure.normalization.runtime import package_version
from module.ingest.extraction.infrastructure.normalization.structure_rules import RULES_VERSION, rules_enabled
from .assembler import assemble
from .checkpoints import CacheLock, FileCheckpointStore, checksum
from .partitioner import SourcePartitioner
from .process_executor import ProcessPartExecutor


async def _io(function, *args):
    # Do not release the cache lock while cancelled filesystem work still runs.
    operation = asyncio.create_task(asyncio.to_thread(function, *args))
    try:
        return await asyncio.shield(operation)
    except asyncio.CancelledError:
        await asyncio.gather(operation, return_exceptions=True)
        raise


class MultipartExtractionEngine(ExtractionEngine):
    """Sequential, checkpointed parts. Each executor owns its process lifetime."""

    def __init__(self, engine: str, configuration: dict | None = None, *, executor: PartExecutor | None = None,
                 partitioner=None, cache_root: Path | None = None):
        settings = (configuration or {}).get('extraction_runtime', {})
        self.engine = engine
        self.pdf_pages = int(settings.get('pdf_pages_per_part', 20))
        self.docx_blocks = int(settings.get('docx_blocks_per_part', 200))
        self.attempts = int(settings.get('part_max_attempts', 2))
        timeout = int(settings.get('part_timeout_seconds', 1800))
        max_bytes = int(settings.get('max_part_artifact_bytes', 64 * 1024 * 1024))
        if min(self.attempts, timeout, max_bytes) < 1:
            raise ValueError('Extraction runtime limits must be positive')
        self.structure_rules = bool(settings.get('structure_rules', rules_enabled()))
        self.partitioner = partitioner or SourcePartitioner(self.pdf_pages, self.docx_blocks)
        self.executor = executor or ProcessPartExecutor(engine, timeout, max_bytes, self.structure_rules)
        self.cache_root = cache_root or Path(os.environ.get('INGEST_EXTRACTION_CACHE_DIR',
                                    str(Path(__file__).resolve().parents[5] / 'temp' / 'extraction-cache')))
        distribution = {'azure_document_intelligence': 'azure-ai-documentintelligence'}.get(engine, engine)
        config = {'abi': 4, 'engine': engine, 'engine_version': package_version(distribution),
                  'partitioner_version': package_version('pypdf'), 'engine_configuration': configuration or {},
                  'pdf_pages': self.pdf_pages, 'docx_blocks': self.docx_blocks,
                  'attempts': self.attempts, 'timeout': timeout, 'max_bytes': max_bytes,
                  'structure_rules': RULES_VERSION if self.structure_rules else None}
        self.fingerprint = hashlib.sha256(json.dumps(config, sort_keys=True, default=str).encode()).hexdigest()

    async def extract(self, file_path: Path) -> ExtractionResult:
        source = Path(file_path).resolve()
        source_hash = await _io(checksum, source)
        directory = self.cache_root.resolve() / source_hash / self.fingerprint
        directory.mkdir(parents=True, exist_ok=True)
        lock = CacheLock(directory / 'cache.lock')
        try:
            while True:
                try:
                    await _io(lock.acquire)
                    break
                except RuntimeError as error:
                    if str(error) != 'Extraction cache is already in use':
                        raise
                    await asyncio.sleep(1)
            store = FileCheckpointStore(directory)
            manifest = await _io(store.load)
            if manifest is None:
                unit, parts = await _io(self.partitioner.plan, source, directory)
                manifest = ExtractionManifest(source_hash, source_hash, self.fingerprint, unit, parts)
                await _io(store.save, manifest)
            elif manifest.source_checksum != source_hash or manifest.configuration_fingerprint != self.fingerprint:
                raise ValueError('Checkpoint identity does not match source/configuration')
            index = 0
            while index < len(manifest.parts):
                part = manifest.parts[index]
                if part.status == PartStatus.PROCESSING:
                    part = replace(part, status=PartStatus.PENDING, attempts=max(0, part.attempts - 1))
                elif part.status == PartStatus.FAILED:
                    # A new invocation may retry a previously failed smallest part.
                    part = replace(part, status=PartStatus.PENDING, attempts=0, error=None)
                if await _io(store.verified_artifact, part):
                    index += 1
                    continue
                # Missing/corrupt completed files are rebuilt; interrupted PROCESSING is retried.
                if part.status == PartStatus.COMPLETED:
                    part = replace(part, status=PartStatus.PENDING, attempts=0,
                                   checksum=None, artifact_path=None)
                fragment = directory / (part.id + source.suffix.lower())
                artifact = directory / (part.id + '.json')
                success = False
                last_error = None
                while part.attempts < self.attempts:
                    part = replace(part, status=PartStatus.PROCESSING, attempts=part.attempts + 1,
                                   error=None, artifact_path=None, checksum=None)
                    manifest = self._replace(manifest, index, part)
                    await _io(store.save, manifest)
                    try:
                        await _io(self.partitioner.materialize, source, part, fragment)
                        await self.executor.execute(fragment, artifact)
                        await _io(self._validate, artifact)
                        part = replace(part, status=PartStatus.COMPLETED,
                                       artifact_path=artifact.name, checksum=await _io(checksum, artifact))
                        success = True
                    except Exception as error:
                        last_error = error
                        part = replace(part, status=PartStatus.FAILED, error=str(error))
                    finally:
                        if fragment.exists():
                            fragment.unlink()
                    manifest = self._replace(manifest, index, part)
                    await _io(store.save, manifest)
                    if success or getattr(last_error, 'retryable', True) is False:
                        break
                    if part.attempts < self.attempts:
                        await asyncio.sleep(min(2 ** part.attempts, 10))
                if success:
                    index += 1
                elif part.source_start < part.source_end and getattr(last_error, 'can_split', True):
                    middle = (part.source_start + part.source_end) // 2
                    children = [ExtractionPart(f'{manifest.source_unit}-{left}-{right}', 0, PartStatus.PENDING, left, right)
                                for left, right in ((part.source_start, middle), (middle + 1, part.source_end))]
                    parts = list(manifest.parts)
                    parts[index:index + 1] = children
                    manifest = replace(manifest, parts=tuple(replace(value, index=i) for i, value in enumerate(parts)))
                    await _io(store.save, manifest)
                else:
                    raise RuntimeError(f'Extraction failed at smallest source range {part.id}: {part.error}')
            header, output = await _io(assemble, directory, manifest, self.engine, source.stem)
            return ExtractionResult(content=header, content_file=output)
        finally:
            lock.release()

    @staticmethod
    def _replace(manifest, index, part):
        values = list(manifest.parts)
        values[index] = part
        return replace(manifest, parts=tuple(values))

    @staticmethod
    def _validate(path):
        payload = json.loads(path.read_text(encoding='utf-8'))
        if payload.get('empty_part') is True:
            if payload.get('schema_version') != 2 or payload.get('blocks') != [] or payload.get('tables') != []:
                raise ValueError('Invalid empty-part artifact')
        else:
            decode_document(payload)
