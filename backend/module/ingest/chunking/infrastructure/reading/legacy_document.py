"""Loss-preserving upgrade for previously persisted section/element output."""
from dataclasses import asdict

from shared.ingestion.document import BlockKind, ContentBlock, DocumentSection, ExtractedTable, SourceLocation, TableCell


def load_legacy(payload, index):
    order = 0

    def text(value, section_id, page, kind=BlockKind.PARAGRAPH):
        nonlocal order
        if value and str(value).strip():
            block = ContentBlock(f'legacy-b{order}', order, kind, SourceLocation(page_number=page),
                                 text=str(value), section_id=section_id)
            index.add_block(asdict(block))
            order += 1

    def table(value, section_id, page):
        nonlocal order
        table_id = f'legacy-t{order}'
        if isinstance(value, dict) and 'rows' in value:
            rows = value['rows']
            cells = tuple(TableCell(r, c, str(cell)) for r, row in enumerate(rows) for c, cell in enumerate(row))
            row_count, column_count = len(rows), max((len(row) for row in rows), default=0)
        else:
            content = value.get('content', '') if isinstance(value, dict) else value
            if not str(content).strip():
                return
            cells = (TableCell(0, 0, str(content)),)
            row_count = column_count = 1
        source = SourceLocation(page_number=page)
        index.add_table(asdict(ExtractedTable(table_id, row_count, column_count, cells, source)))
        index.add_block(asdict(ContentBlock(f'legacy-b{order}', order, BlockKind.TABLE,
                                           source, table_id=table_id, section_id=section_id)))
        order += 1

    def visit(sections, parent=None, parent_level=0):
        for number, section in enumerate(sections or []):
            section_id = f'{parent or "legacy"}-s{number}'
            title = str(section.get('title') or 'Untitled')
            level = max(parent_level + 1, int(section.get('level') or 1))
            index.add_section(asdict(DocumentSection(section_id, title, level, parent)))
            page = section.get('page_no') or None
            if title.upper() not in {'ROOT', 'UNTITLED'}:
                text(title, section_id, page, BlockKind.HEADING)
            content = section.get('content')
            if not content and not section.get('children'):
                content = section.get('aggregated_content')
            text(content, section_id, page)
            for item in section.get('tables') or []:
                table(item, section_id, page)
            visit(section.get('children'), section_id, level)

    if 'sections' in payload:
        visit(payload['sections'])
    elif 'elements' in payload:
        for element in payload['elements']:
            page = element.get('page_no') or None
            if element.get('type') == 'table':
                table(element, None, page)
            else:
                text(element.get('content') or element.get('text'), None, page)
    else:
        text(payload.get('text') or payload.get('content'), None, None)
