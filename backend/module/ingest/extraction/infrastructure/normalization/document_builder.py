from dataclasses import asdict
import json

from shared.ingestion.document import (
    BlockKind, ContentBlock, DocumentSection, ExtractedDocumentV2,
    ExtractedTable, ExtractionMetadata, SourceLocation, StructureQuality,
)
from .structure_rules import APPLIED_WARNING, resolve_levels, rules_enabled


class NormalizedDocumentBuilder:
    """Preserve reading order before adding optional semantic sections."""

    def __init__(self, document_id: str, title: str, engine: str, version: str,
                 structure_rules: bool | None = None):
        self.document_id = document_id
        self.title = title
        self.engine = engine
        self.version = version
        self.blocks: list[ContentBlock] = []
        self.tables: list[ExtractedTable] = []
        self.sections: list[DocumentSection] = []
        self.warnings: list[str] = []
        self._stack: list[DocumentSection] = []
        # With rules on, items wait for build() so headings are judged against the whole run.
        self._pending: list | None = [] if (rules_enabled() if structure_rules is None else structure_rules) else None

    def add_text(self, text: str, source: SourceLocation, *, level: int | None = None,
                 kind: BlockKind = BlockKind.PARAGRAPH) -> None:
        if not text.strip():
            return
        if self._pending is not None:
            self._pending.append((text, source, level, kind))
            return
        self._emit_text(text, source, level, kind)

    def _emit_text(self, text: str, source: SourceLocation, level: int | None, kind: BlockKind,
                   title: str | None = None) -> None:
        if level is not None:
            while self._stack and self._stack[-1].level >= level:
                self._stack.pop()
            section = DocumentSection(
                f"s{len(self.sections)}", f"{text} - {title}" if title else text, level,
                self._stack[-1].id if self._stack else None,
            )
            self.sections.append(section)
            self._stack.append(section)
            kind = BlockKind.HEADING
        self.blocks.append(ContentBlock(
            f"b{len(self.blocks)}", len(self.blocks), kind, source, text=text,
            section_id=self._stack[-1].id if self._stack else None,
        ))

    def add_table(self, table: ExtractedTable) -> None:
        self.tables.append(table)  # providers derive the next table ID from len(tables)
        if self._pending is not None:
            self._pending.append(table)
            return
        self._emit_table(table)

    def _emit_table(self, table: ExtractedTable) -> None:
        self.blocks.append(ContentBlock(
            f"b{len(self.blocks)}", len(self.blocks), BlockKind.TABLE, table.source,
            table_id=table.id, section_id=self._stack[-1].id if self._stack else None,
        ))

    def _flush(self) -> None:
        pending, self._pending = self._pending, None
        texts = [item for item in pending if isinstance(item, tuple)]
        resolution = resolve_levels([item[0] for item in texts], [item[2] for item in texts])
        if resolution is not None and APPLIED_WARNING not in self.warnings:
            self.warnings.append(APPLIED_WARNING)
        position = 0
        for item in pending:
            if not isinstance(item, tuple):
                self._emit_table(item)
                continue
            text, source, level, kind = item
            if resolution is not None:
                level = resolution.levels[position]
            self._emit_text(text, source, level, kind,
                            resolution.titles.get(position) if resolution is not None else None)
            position += 1

    def build(self) -> ExtractedDocumentV2:
        if self._pending is not None:
            self._flush()
        quality = StructureQuality.FLAT
        if self.sections:
            quality = (StructureQuality.STRUCTURED if all(b.section_id for b in self.blocks)
                       else StructureQuality.PARTIAL)
        return ExtractedDocumentV2(
            self.document_id, self.title,
            ExtractionMetadata(self.engine, self.version, quality, tuple(self.warnings)),
            tuple(self.blocks), tuple(self.tables), tuple(self.sections),
        )


def serialize_document(document: ExtractedDocumentV2) -> dict:
    """V2 is authoritative; temporary legacy projection supports old consumers.

    Every block occurs once in this projection. Flat blocks receive a synthetic
    section; the authoritative V2 does not invent semantic headings.
    """
    payload = asdict(document)
    tables = {table.id: table for table in document.tables}
    legacy = []
    for block in document.blocks:
        table = tables.get(block.table_id)
        content = block.text
        if table is not None:
            content = json.dumps(asdict(table), ensure_ascii=False)
        legacy.append({
            "id": block.id, "title": block.text if block.kind == BlockKind.HEADING else "ROOT",
            "level": 2, "content": content, "aggregated_content": content,
            "token_count": len(content.split()), "aggregated_token_count": len(content.split()),
            "page_no": block.source.page_number, "tables": [], "children": [], "images": [],
        })
    payload["legacy_sections"] = legacy
    return payload
