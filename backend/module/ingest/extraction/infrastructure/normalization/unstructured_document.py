from shared.ingestion.document import ExtractedTable, SourceLocation, TableCell
from .document_builder import NormalizedDocumentBuilder
from .html_table import HtmlTableReader


def normalize_unstructured(elements, *, document_id: str, title: str, version: str):
    builder = NormalizedDocumentBuilder(document_id, title, "unstructured", version)
    for element in elements:
        category = getattr(element, "category", type(element).__name__)
        metadata = getattr(element, "metadata", None)
        source = SourceLocation(page_number=getattr(metadata, "page_number", None))
        text = getattr(element, "text", "") or ""
        if category == "Table":
            html = getattr(metadata, "text_as_html", None)
            if html:
                table = HtmlTableReader().read(html, table_id=f"t{len(builder.tables)}", source=source)
            elif text.strip():
                builder.warnings.append("Table grid unavailable; preserved text in a single cell, not an inferred grid")
                table = ExtractedTable(f"t{len(builder.tables)}", 1, 1,
                                       (TableCell(0, 0, text),), source)
            else:
                raise ValueError("Provider returned an empty table")
            builder.add_table(table)
        elif category in {"Image", "PageBreak"}:
            continue
        else:
            depth = getattr(metadata, "category_depth", None)
            level = max(1, int(depth) + 1) if category == "Title" and depth is not None else (1 if category == "Title" else None)
            builder.add_text(text, source, level=level)
    return builder.build()
