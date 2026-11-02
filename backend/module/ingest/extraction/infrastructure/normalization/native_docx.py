"""Read Word text and tables directly, independently of heading recognition.

No OCR, rendering, external SDK or layout model is required. Nested table text
is preserved in its containing cell with an explicit warning.
"""
import re
from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import ZipFile

from shared.ingestion.document import BlockKind, ExtractedTable, SourceLocation, TableCell
from .document_builder import NormalizedDocumentBuilder

NS = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"


def _value(element, name: str, default=None):
    child = element.find(name) if element is not None else None
    return child.get(NS + "val", default) if child is not None else default


def _text(element) -> str:
    parts = []
    for node in element.iter():
        if node.tag == NS + "t":
            parts.append(node.text or "")
        elif node.tag == NS + "tab":
            parts.append("\t")
        elif node.tag in {NS + "br", NS + "cr"}:
            parts.append("\n")
        elif node.tag == NS + "p" and parts:
            parts.append("\n")
    return "".join(parts).strip()


class NativeDocxReader:
    def read(self, file_path: Path):
        with ZipFile(file_path) as archive:
            root = ET.fromstring(archive.read("word/document.xml"))
            title = file_path.stem
            if "docProps/core.xml" in archive.namelist():
                title_node = ET.fromstring(archive.read("docProps/core.xml")).find(
                    "{http://purl.org/dc/elements/1.1/}title")
                if title_node is not None and (title_node.text or "").strip():
                    title = title_node.text.strip()
            styles = {}
            if "word/styles.xml" in archive.namelist():
                for style in ET.fromstring(archive.read("word/styles.xml")).findall(NS + "style"):
                    styles[style.get(NS + "styleId")] = style
        builder = NormalizedDocumentBuilder(file_path.stem, title, "native-docx", "2")
        body = root.find(NS + "body")
        if body is None:
            raise ValueError("DOCX has no document body")
        for index, node in enumerate(self._blocks(body)):
            source = SourceLocation(native_block_index=index)
            if node.tag == NS + "tbl":
                if node.findall(".//" + NS + "tbl"):
                    builder.warnings.append("Nested table text retained in parent cell; nested grid not modeled")
                builder.add_table(self._table(node, f"t{len(builder.tables)}", source))
            else:
                level = self._heading_level(node, styles)
                kind = BlockKind.LIST_ITEM if node.find(NS + "pPr/" + NS + "numPr") is not None else BlockKind.PARAGRAPH
                builder.add_text(_text(node), source, level=level, kind=kind)
        if root.findall(".//" + NS + "drawing") or root.findall(".//" + NS + "pict"):
            builder.warnings.append("Embedded images were not processed; text/table extraction only")
        builder.warnings.append("Headers, footers, comments and tracked deletions are outside body extraction scope")
        return builder.build()

    def _blocks(self, parent):
        for node in parent:
            if node.tag in {NS + "p", NS + "tbl"}:
                yield node
            elif node.tag not in {NS + "del", NS + "sectPr"}:
                yield from self._blocks(node)

    def _heading_level(self, paragraph, styles):
        properties = paragraph.find(NS + "pPr")
        outline = _value(properties, NS + "outlineLvl")
        style_id = _value(properties, NS + "pStyle")
        visited = set()
        while outline is None and style_id and style_id not in visited:
            visited.add(style_id)
            style = styles.get(style_id)
            if style is None:
                break
            outline = _value(style.find(NS + "pPr"), NS + "outlineLvl")
            name = _value(style, NS + "name", style_id)
            match = re.fullmatch(r"heading\s*([1-9])", name, re.IGNORECASE)
            if outline is None and match:
                return int(match.group(1))
            style_id = _value(style, NS + "basedOn")
        if outline is not None and 0 <= int(outline) <= 8:
            return int(outline) + 1
        return None

    def _table(self, node, table_id, source):
        rows = node.findall(NS + "tr")
        cells = []
        previous_merges = {}
        width = len(node.findall(NS + "tblGrid/" + NS + "gridCol"))
        header_rows = []
        for row_index, row in enumerate(rows):
            row_props = row.find(NS + "trPr")
            header = row_props.find(NS + "tblHeader") if row_props is not None else None
            is_header = header is not None and header.get(NS + "val", "true") not in {"0", "false", "off"}
            if is_header:
                header_rows.append(row_index)
            column = int(_value(row_props, NS + "gridBefore", "0"))
            current_merges = {}
            for cell in row.findall(NS + "tc"):
                props = cell.find(NS + "tcPr")
                span = int(_value(props, NS + "gridSpan", "1"))
                merge = props.find(NS + "vMerge") if props is not None else None
                text = _text(cell)
                key = (column, span)
                if merge is not None and merge.get(NS + "val", "continue") == "continue":
                    if key not in previous_merges:
                        raise ValueError("DOCX table has orphan vertical merge continuation")
                    anchor = previous_merges[key]
                    cells[anchor]["row_span"] += 1
                    if text:
                        cells[anchor]["text"] += "\n" + text
                    current_merges[key] = anchor
                else:
                    cells.append(dict(row=row_index, column=column, text=text,
                                      row_span=1, column_span=span, is_header=is_header))
                    if merge is not None:
                        current_merges[key] = len(cells) - 1
                column += span
            width = max(width, column + int(_value(row_props, NS + "gridAfter", "0")))
            previous_merges = current_merges
        return ExtractedTable(table_id, len(rows), width,
                              tuple(TableCell(**cell) for cell in cells), source,
                              header_rows=tuple(header_rows) if header_rows else None)
