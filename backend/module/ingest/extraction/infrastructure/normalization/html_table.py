from html.parser import HTMLParser

from shared.ingestion.document import ExtractedTable, TableCell


class HtmlTableReader(HTMLParser):
    """Preserve provider HTML cells and spans; reject nested grids explicitly."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.rows = []
        self.cell = None
        self.depth = 0

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        if tag == "table":
            self.depth += 1
            if self.depth > 1:
                raise ValueError("Nested HTML tables require a dedicated adapter")
        elif tag == "tr":
            self.rows.append([])
        elif tag in {"td", "th"}:
            if not self.rows or self.cell is not None:
                raise ValueError("Malformed HTML table")
            self.cell = {"text": "", "row_span": int(values.get("rowspan", 1)),
                         "column_span": int(values.get("colspan", 1)), "is_header": tag == "th"}
        elif tag in {"br", "p"} and self.cell is not None:
            self.cell["text"] += "\n"

    def handle_endtag(self, tag):
        if tag in {"td", "th"} and self.cell is not None:
            self.rows[-1].append(self.cell)
            self.cell = None
        elif tag == "table":
            self.depth -= 1

    def handle_data(self, data):
        if self.cell is not None:
            self.cell["text"] += data

    def read(self, html, *, table_id, source):
        self.feed(html)
        self.close()
        if self.cell is not None:
            raise ValueError("Unclosed HTML table cell")
        cells = []
        width = 0
        for row_index, row in enumerate(self.rows):
            column = 0
            for raw in row:
                while any(cell.row <= row_index < cell.row + cell.row_span
                          and cell.column <= column < cell.column + cell.column_span for cell in cells):
                    column += 1
                cell = TableCell(row=row_index, column=column, **raw)
                cells.append(cell)
                column += cell.column_span
            width = max(width, column)
        return ExtractedTable(table_id, len(self.rows), width, tuple(cells), source,
                              header_rows=tuple(sorted({cell.row for cell in cells if cell.is_header})) or None)
