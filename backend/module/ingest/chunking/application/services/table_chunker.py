import json
from collections.abc import Iterator
from shared.ingestion.document import ContentBlock, ExtractedTable

from module.ingest.chunking.domain.contracts.chunking_engine import Chunk
from module.ingest.chunking.domain.contracts.document_reader import CoverageRecorder
from .chunk_budget import fitting_prefix, provenance


def _cell(cell):
    result = {'row': cell.row, 'column': cell.column, 'text': cell.text}
    if cell.row_span != 1:
        result['row_span'] = cell.row_span
    if cell.column_span != 1:
        result['column_span'] = cell.column_span
    return result


def _json(payload):
    return json.dumps(payload, ensure_ascii=False, separators=(',', ':'))


class TableChunker:
    def __init__(self, budget):
        self.budget = budget

    def chunks(self, block: ContentBlock, table: ExtractedTable, heading_path: tuple[str, ...],
               coverage: CoverageRecorder) -> Iterator[Chunk]:
        base = provenance(block, heading_path)
        headers = [cell for cell in table.cells if cell.row in (table.header_rows or ())]
        header_keys = {(cell.row, cell.column) for cell in headers}
        spanning = sorted((cell for cell in table.cells if cell.row_span > 1
                           and (cell.row, cell.column) not in header_keys), key=lambda cell: cell.row)
        span_position = 0
        carry_start = -1
        carry_active = []
        by_row = {}
        for cell in table.cells:
            by_row.setdefault(cell.row, []).append(cell)

        if table.caption:
            position = 0
            while position < len(table.caption):
                def caption(value):
                    payload = {'table_id': table.id, 'caption_fragment': {
                        'start': position, 'end': position + len(value), 'text': value}}
                    metadata = {**base, 'caption_slice': {'table_id': table.id,
                                 'start': position, 'end': position + len(value)}}
                    return _json(payload), metadata
                size = fitting_prefix(table.caption[position:], lambda value: self.budget.fits(*caption(value)))
                content, metadata = caption(table.caption[position:position + size])
                coverage.record_caption(table.id, position, position + size,
                                        json.loads(content)['caption_fragment']['text'])
                yield Chunk(-1, None, content, metadata)
                position += size

        def grouped(start, end):
            nonlocal span_position, carry_start, carry_active
            own = [cell for row in range(start, end) for cell in by_row.get(row, ())]
            if carry_start != start:
                while span_position < len(spanning) and spanning[span_position].row < start:
                    carry_active.append(spanning[span_position])
                    span_position += 1
                carry_active = [cell for cell in carry_active if cell.row + cell.row_span > start]
                carry_start = start
            payload = {'table_id': table.id, 'row_range': [start, end],
                       'headers': [_cell(cell) for cell in headers],
                       'cells': [_cell(cell) for cell in own if (cell.row, cell.column) not in header_keys]}
            if table.caption:
                payload['caption_context'] = table.caption[:120]
            if carry_active:
                payload['carry_cells'] = [_cell(cell) for cell in carry_active]
            metadata = {**base, 'table_slices': [{'table_id': table.id, 'row_start': start, 'row_end': end}]}
            return _json(payload), metadata, own

        start = 0
        while start < table.row_count:
            content, metadata, own = grouped(start, start + 1)
            if not self.budget.fits(content, metadata):
                # A row (or header context) can exceed the budget. Preserve each
                # canonical cell as explicit fragments instead of dropping it.
                cells = by_row.get(start, [])
                coverage.record_rows(table.id, start, start + 1)
                if not cells:
                    payload = {'table_id': table.id, 'row_range': [start, start + 1],
                               'cells': [], 'header_reference_only': True}
                    content = _json(payload)
                    if not self.budget.fits(content, metadata):
                        raise ValueError('Chunk budget cannot fit an empty table row with provenance')
                    yield Chunk(-1, None, content, metadata)
                for cell in cells:
                    position = 0
                    first = True
                    while position < len(cell.text) or first:
                        first = False

                        def fragment(value, include_headers=True):
                            entry = {**_cell(cell), 'text': value, 'start': position, 'end': position + len(value)}
                            payload = {'table_id': table.id, 'cell_fragment': entry}
                            if include_headers:
                                payload['headers'] = [_cell(item) for item in headers]
                            else:
                                payload['header_reference_only'] = True
                            fragment_metadata = {**base, 'cell_slice': {'table_id': table.id, 'row': cell.row,
                                'column': cell.column, 'start': position, 'end': position + len(value)}}
                            return _json(payload), fragment_metadata

                        include = self.budget.fits(*fragment('', True))
                        # If full headers leave no room for actual data, use an
                        # explicit reference. Header source cells are emitted too.
                        if cell.text[position:] and not self.budget.fits(*fragment(cell.text[position:position + 1], include)):
                            include = False
                        remaining = cell.text[position:]
                        size = fitting_prefix(remaining, lambda value: self.budget.fits(*fragment(value, include))) if remaining else 0
                        content, fragment_metadata = fragment(remaining[:size], include)
                        if not self.budget.fits(content, fragment_metadata):
                            raise ValueError('Chunk budget cannot fit table cell provenance')
                        coverage.record_cell(table.id, cell.row, cell.column, position, position + size,
                                             json.loads(content)['cell_fragment']['text'])
                        yield Chunk(-1, None, content, fragment_metadata)
                        position += size
                start += 1
                continue
            end = start + 1
            while end < table.row_count:
                candidate = grouped(start, end + 1)
                if not self.budget.fits(candidate[0], candidate[1]):
                    break
                content, metadata, own = candidate
                end += 1
            coverage.record_rows(table.id, start, end)
            emitted = json.loads(content)
            emitted_cells = {(cell['row'], cell['column']): cell for cell in emitted['headers'] + emitted['cells']}
            for cell in own:
                coverage.record_cell(table.id, cell.row, cell.column, 0, len(cell.text),
                                     emitted_cells[(cell.row, cell.column)]['text'])
            yield Chunk(-1, None, content, metadata)
            start = end
