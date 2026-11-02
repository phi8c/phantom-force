import asyncio
import json
import os
from pathlib import Path
import subprocess
import sys

from module.ingest.extraction.domain.contracts.extraction_parts import PartExecutionError
from module.ingest.extraction.infrastructure.normalization.structure_rules import ENV_FLAG


class ProcessPartExecutor:
    def __init__(self, engine: str, timeout_seconds: int = 1800, max_artifact_bytes: int = 64 * 1024 * 1024,
                 structure_rules: bool | None = None):
        self.engine = engine
        self.environment = None if structure_rules is None else {**os.environ, ENV_FLAG: '1' if structure_rules else '0'}
        self.timeout_seconds = timeout_seconds
        self.max_artifact_bytes = max_artifact_bytes

    async def execute(self, source: Path, destination: Path):
        backend = Path(__file__).resolve().parents[5]
        destination.with_suffix('.error.json').unlink(missing_ok=True)
        with destination.with_suffix('.log').open('wb') as log:
            process = await asyncio.create_subprocess_exec(
                sys.executable, '-c',
                'import runpy,sys;sys.path.insert(0,sys.argv[1]);runpy.run_module("module.ingest.extraction.infrastructure.multipart.part_worker",run_name="__main__")',
                str(backend),
                cwd=str(backend), env=self.environment, stdin=asyncio.subprocess.PIPE, stdout=log, stderr=log,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0,
            )
            try:
                request = json.dumps({'engine': self.engine, 'source': str(source.resolve()),
                                      'destination': str(destination.resolve())}).encode()
                await asyncio.wait_for(process.communicate(request), timeout=self.timeout_seconds)
                if process.returncode:
                    error_path = destination.with_suffix('.error.json')
                    if error_path.is_file():
                        error = json.loads(error_path.read_text(encoding='utf-8'))
                        raise PartExecutionError(error['message'], can_split=error['can_split'], retryable=error['retryable'])
                    raise PartExecutionError(f'Extraction process exited with code {process.returncode}; see {destination.with_suffix(".log").name}')
                if not destination.is_file() or destination.stat().st_size > self.max_artifact_bytes:
                    raise PartExecutionError('Part output missing or larger than configured artifact limit')
            except asyncio.TimeoutError as error:
                if process.returncode is None:
                    process.kill()
                    await process.wait()
                raise PartExecutionError('Extraction part exceeded its time budget') from error
            except BaseException:
                if process.returncode is None:
                    process.kill()
                    await process.wait()
                raise
