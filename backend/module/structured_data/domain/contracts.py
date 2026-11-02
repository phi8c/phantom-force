from pathlib import Path
from datetime import datetime
from typing import Protocol
from uuid import UUID

from .models import BuiltDataset, Dataset, QueryResult


class WorkbookBuilder(Protocol):
    def build(self, source: Path, output: Path, *, space: UUID, document: UUID,
              file_name: str, configuration: dict) -> list[BuiltDataset]: ...


class Catalog(Protocol):
    async def ensure_ready(self) -> None: ...
    async def publish(self, space: UUID, document: UUID, datasets: list[Dataset], embeddings: list[list[float]],
                      *, job_id: UUID, run_created_at: datetime) -> None: ...
    async def has_datasets(self, space: UUID) -> bool: ...
    async def search(self, space: UUID, vector: list[float], limit: int = 4) -> list[Dataset]: ...


class ArtifactStore(Protocol):
    async def upload(self, path: str, source: Path, content_type: str) -> None: ...
    async def download(self, path: str, destination: Path, checksum: str) -> None: ...


class QueryPlanner(Protocol):
    async def plan(self, question: str, candidates: list[Dataset], feedback: str | None = None) -> dict | None: ...


class StructuredQueryEngine(Protocol):
    def execute(self, plan: dict, datasets: list[Dataset], paths: dict[UUID, Path]) -> QueryResult: ...
