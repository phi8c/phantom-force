from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any
from uuid import UUID


@dataclass(frozen=True)
class Column:
    key: str
    name: str
    data_type: str
    source_column: int
    statistics: dict[str, Any] = field(default_factory=dict)
    number_format: str | None = None
    description: str | None = None


@dataclass(frozen=True)
class Dataset:
    id: UUID
    knowledge_space_id: UUID
    document_id: UUID
    version: str
    file_name: str
    sheet: str
    source_range: str
    name: str
    columns: tuple[Column, ...]
    row_count: int
    parquet_path: str
    parquet_sha256: str
    warnings: tuple[str, ...] = ()
    formulas_path: str | None = None
    description: str | None = None
    relationships: tuple[dict, ...] = ()

    def descriptor(self):
        return {'dataset_id': str(self.id), 'document_id': str(self.document_id),
                'version': self.version, 'file_name': self.file_name, 'sheet': self.sheet,
                'source_range': self.source_range, 'name': self.name, 'description':self.description,'row_count': self.row_count,
                'columns': [asdict(c) for c in self.columns], 'warnings': list(self.warnings),
                'relationships':list(self.relationships)}


@dataclass(frozen=True)
class BuiltDataset:
    dataset: Dataset
    parquet: Path
    formulas: Path | None = None


@dataclass(frozen=True)
class QueryResult:
    columns: tuple[str, ...]
    rows: tuple[tuple[Any, ...], ...]
    sources: tuple[dict, ...]
    truncated: bool
    plan: dict
    chart: dict | None = None
    row_sources: tuple[dict, ...] = ()
    column_metadata: dict[str, dict] = field(default_factory=dict)

    def payload(self):
        return asdict(self)
