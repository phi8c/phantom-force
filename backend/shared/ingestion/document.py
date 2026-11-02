"""V2 interchange types. IDs and reading order are document-global.

Missing hierarchy is valid; silently accepting empty extraction is not.
This shared kernel has no dependencies on ingestion modules or providers.
"""
from dataclasses import dataclass
from enum import Enum


class BlockKind(str, Enum):
    PARAGRAPH = "paragraph"
    HEADING = "heading"
    LIST_ITEM = "list_item"
    TABLE = "table"


class StructureQuality(str, Enum):
    STRUCTURED = "structured"
    PARTIAL = "partial"
    FLAT = "flat"


@dataclass(frozen=True)
class SourceLocation:
    page_number: int | None = None
    native_block_index: int | None = None
    part_id: str | None = None

    def __post_init__(self):
        if self.page_number is not None and self.page_number < 1:
            raise ValueError("page_number must be one-based")
        if self.native_block_index is not None and self.native_block_index < 0:
            raise ValueError("native_block_index must be nonnegative")


@dataclass(frozen=True)
class TableCell:
    row: int
    column: int
    text: str
    row_span: int = 1
    column_span: int = 1
    is_header: bool = False

    def __post_init__(self):
        if min(self.row, self.column) < 0 or min(self.row_span, self.column_span) < 1:
            raise ValueError("Invalid cell position or span")


@dataclass(frozen=True)
class ExtractedTable:
    id: str
    row_count: int
    column_count: int
    cells: tuple[TableCell, ...]
    source: SourceLocation
    caption: str | None = None
    # None means unknown; () means explicitly no header rows.
    header_rows: tuple[int, ...] | None = None

    def __post_init__(self):
        if not self.id or min(self.row_count, self.column_count) < 1 or not self.cells:
            raise ValueError("Table requires ID, positive dimensions and cells")
        active: list[TableCell] = []
        for cell in sorted(self.cells, key=lambda item: (item.row, item.column)):
            if (cell.row + cell.row_span > self.row_count
                    or cell.column + cell.column_span > self.column_count):
                raise ValueError("Cell extends beyond table dimensions")
            active = [other for other in active if other.row + other.row_span > cell.row]
            if any(cell.column < other.column + other.column_span
                   and other.column < cell.column + cell.column_span for other in active):
                raise ValueError("Overlapping table cells")
            active.append(cell)
        for row in self.header_rows or ():
            if not 0 <= row < self.row_count:
                raise ValueError("Header row outside table")


@dataclass(frozen=True)
class ContentBlock:
    id: str
    order: int
    kind: BlockKind
    source: SourceLocation
    text: str = ""
    table_id: str | None = None
    section_id: str | None = None

    def __post_init__(self):
        if not self.id or self.order < 0:
            raise ValueError("Block requires ID and nonnegative order")
        if not isinstance(self.kind, BlockKind):
            raise ValueError("Unknown block kind")
        if self.kind == BlockKind.TABLE:
            if not self.table_id:
                raise ValueError("Table block requires table_id")
        elif not self.text.strip() or self.table_id is not None:
            raise ValueError("Text block requires text and cannot reference a table")


@dataclass(frozen=True)
class DocumentSection:
    id: str
    title: str
    level: int
    parent_id: str | None = None

    def __post_init__(self):
        if not self.id or not self.title.strip() or self.level < 1:
            raise ValueError("Invalid document section")


@dataclass(frozen=True)
class ExtractionMetadata:
    engine: str
    engine_version: str
    structure_quality: StructureQuality
    warnings: tuple[str, ...] = ()


@dataclass(frozen=True)
class ExtractedDocumentV2:
    document_id: str
    title: str
    extraction: ExtractionMetadata
    blocks: tuple[ContentBlock, ...]
    tables: tuple[ExtractedTable, ...] = ()
    sections: tuple[DocumentSection, ...] = ()
    schema_version: int = 2

    def __post_init__(self):
        if self.schema_version != 2 or not self.document_id:
            raise ValueError("Expected schema_version=2 and document_id")
        if not self.blocks:
            raise ValueError("Extraction contains no content blocks")
        _unique(tuple(block.id for block in self.blocks), "block IDs")
        _unique(tuple(table.id for table in self.tables), "table IDs")
        _unique(tuple(section.id for section in self.sections), "section IDs")
        orders = tuple(block.order for block in self.blocks)
        if orders != tuple(sorted(set(orders))):
            raise ValueError("Blocks require unique, increasing reading order")
        sections = {section.id: section for section in self.sections}
        for section in self.sections:
            if section.parent_id is not None:
                parent = sections.get(section.parent_id)
                if parent is None or parent.level >= section.level:
                    raise ValueError("Section parent must exist at a lower level")
        references = []
        for block in self.blocks:
            if block.section_id is not None and block.section_id not in sections:
                raise ValueError("Unknown section reference")
            if block.kind == BlockKind.TABLE:
                references.append(block.table_id)
        _unique(tuple(references), "table block references")
        if set(references) != {table.id for table in self.tables}:
            raise ValueError("Every table requires exactly one ordered table block")
        if not any(block.text.strip() for block in self.blocks) and not any(
            cell.text.strip() for table in self.tables for cell in table.cells
        ):
            raise ValueError("Extraction contains no readable text")


def _unique(values: tuple, name: str) -> None:
    if len(set(values)) != len(values):
        raise ValueError(f"Duplicate {name}")
