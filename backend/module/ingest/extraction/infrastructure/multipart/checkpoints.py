import hashlib
import json
import os
from dataclasses import asdict
from pathlib import Path

from shared.ingestion.parts import ExtractionManifest, ExtractionPart, PartStatus


def checksum(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open('rb') as source:
        for block in iter(lambda: source.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def atomic_json(path: Path, payload) -> None:
    temporary = path.with_suffix(path.suffix + '.tmp')
    with temporary.open('w', encoding='utf-8') as target:
        json.dump(payload, target, ensure_ascii=False)
        target.flush()
        os.fsync(target.fileno())
    os.replace(temporary, path)


class FileCheckpointStore:
    def __init__(self, directory: Path):
        self.directory = directory
        self.path = directory / 'manifest.json'

    def load(self) -> ExtractionManifest | None:
        if not self.path.exists():
            return None
        data = json.loads(self.path.read_text(encoding='utf-8'))
        data['parts'] = tuple(ExtractionPart(**{**part, 'status': PartStatus(part['status'])})
                              for part in data['parts'])
        return ExtractionManifest(**data)

    def save(self, manifest: ExtractionManifest) -> None:
        atomic_json(self.path, asdict(manifest))

    def verified_artifact(self, part: ExtractionPart) -> bool:
        if part.status != PartStatus.COMPLETED or not part.artifact_path:
            return False
        artifact = self.directory / part.artifact_path
        if artifact.resolve().parent != self.directory.resolve():
            raise ValueError('Checkpoint artifact must stay within its cache directory')
        return artifact.is_file() and checksum(artifact) == part.checksum


class CacheLock:
    """OS releases the lock if a worker dies; persistent files are not stale locks."""

    def __init__(self, path: Path):
        self.path = path
        self.file = None

    def acquire(self):
        self.file = self.path.open('a+b')
        self.file.seek(0)
        if os.name == 'nt':
            import msvcrt
            self.file.write(b'0')
            self.file.flush()
            self.file.seek(0)
            try:
                msvcrt.locking(self.file.fileno(), msvcrt.LK_NBLCK, 1)
            except OSError:
                self.file.close()
                self.file = None
                raise RuntimeError('Extraction cache is already in use')
        else:
            import fcntl
            try:
                fcntl.flock(self.file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            except OSError:
                self.file.close()
                self.file = None
                raise RuntimeError('Extraction cache is already in use')

    def release(self):
        if self.file is not None:
            self.file.close()
            self.file = None
