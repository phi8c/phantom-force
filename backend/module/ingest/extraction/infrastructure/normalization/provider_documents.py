"""Translate provider primitives into the common text/table model."""
from shared.ingestion.document import ExtractedTable, SourceLocation, TableCell
from .document_builder import NormalizedDocumentBuilder


def normalize_docling(document, *, document_id: str, version: str):
    builder = NormalizedDocumentBuilder(document_id, getattr(document, "name", document_id), "docling", version)
    for item, _ in document.iterate_items():
        raw_label = getattr(item, "label", "")
        label = getattr(raw_label, "value", raw_label)
        provenance = getattr(item, "prov", None) or []
        source = SourceLocation(page_number=provenance[0].page_no if provenance else None)
        if label == "table":
            data = item.data
            cells = tuple(TableCell(
                row=cell.start_row_offset_idx, column=cell.start_col_offset_idx,
                text=cell.text, row_span=cell.row_span, column_span=cell.col_span,
                is_header=cell.column_header,
            ) for cell in data.table_cells)
            headers = tuple(sorted({cell.row for cell in cells if cell.is_header}))
            builder.add_table(ExtractedTable(
                f"t{len(builder.tables)}", data.num_rows, data.num_cols, cells, source,
                header_rows=headers or None,
            ))
        elif label == "picture":
            builder.warnings.append("Picture omitted; OCR/image extraction is disabled")
        elif hasattr(item, "text"):
            level = max(1, int(getattr(item, "level", 1))) if label == "section_header" else None
            builder.add_text(item.text, source, level=level)
    return builder.build()


def normalize_azure(result, *, document_id: str, title: str, version: str):
    builder = NormalizedDocumentBuilder(document_id, title, "azure_document_intelligence", version)
    items = []
    table_spans = []
    for table in result.tables or []:
        spans = [(span.offset, span.offset + span.length) for span in table.spans or []]
        table_spans.extend(spans)
        items.append((min((start for start, _ in spans), default=-1), "table", table))
    for paragraph in result.paragraphs or []:
        spans = [(span.offset, span.offset + span.length) for span in paragraph.spans or []]
        if spans and all(any(start >= left and end <= right for left, right in table_spans)
                         for start, end in spans):
            continue
        items.append((min((start for start, _ in spans), default=-1), "paragraph", paragraph))
    if any(offset < 0 for offset, _, _ in items):
        builder.warnings.append("Provider omitted offsets; reading order is approximate for those blocks")
    for _, kind, item in sorted(items, key=lambda value: value[0]):
        regions = item.bounding_regions or []
        source = SourceLocation(page_number=regions[0].page_number if regions else None)
        if kind == "table":
            cells = tuple(TableCell(
                cell.row_index, cell.column_index, cell.content or "",
                cell.row_span or 1, cell.column_span or 1,
                str(getattr(cell.kind, "value", cell.kind)) == "columnHeader",
            ) for cell in item.cells)
            builder.add_table(ExtractedTable(
                f"t{len(builder.tables)}", item.row_count, item.column_count, cells, source,
                header_rows=tuple(sorted({cell.row for cell in cells if cell.is_header})) or None,
            ))
        else:
            role = getattr(item.role, "value", item.role)
            builder.add_text(item.content, source, level=1 if role in {"title", "sectionHeading"} else None)
    if not items and getattr(result, "content", "").strip():
        builder.warnings.append("No layout blocks returned; using provider plain text")
        builder.add_text(result.content, SourceLocation())
    return builder.build()
