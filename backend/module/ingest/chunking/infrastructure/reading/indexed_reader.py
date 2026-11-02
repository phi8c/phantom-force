from contextlib import contextmanager
import json
from pathlib import Path
import sqlite3
import tempfile

from shared.ingestion.document import BlockKind, ContentBlock, DocumentSection, ExtractedTable, SourceLocation, TableCell
from .json_items import JsonObjectItems


def decode_block(raw):
    return ContentBlock(**{**raw, 'kind': BlockKind(raw['kind']), 'source': SourceLocation(**raw['source'])})


def decode_table(raw):
    return ExtractedTable(**{**raw, 'source': SourceLocation(**raw['source']),
        'cells': tuple(TableCell(**cell) for cell in raw['cells']),
        'header_rows': tuple(raw['header_rows']) if raw.get('header_rows') is not None else None})


def _key(*parts):
    return json.dumps(parts, separators=(',', ':'))


class IndexedDocument:
    def __init__(self, connection):
        self.db = connection
        self.previous_order = -1
        self.readable = False
        self.title = None
        self.db.executescript('''
          PRAGMA journal_mode=OFF; PRAGMA temp_store=FILE; PRAGMA cache_size=-2048;
          CREATE TABLE blocks(id TEXT PRIMARY KEY, ordinal INTEGER UNIQUE, kind TEXT,
                              table_id TEXT, section_id TEXT, payload TEXT);
          CREATE TABLE tables(id TEXT PRIMARY KEY, payload TEXT);
          CREATE TABLE sections(id TEXT PRIMARY KEY, parent_id TEXT, level INTEGER, title TEXT);
          CREATE TABLE coverage(id TEXT PRIMARY KEY, text TEXT NOT NULL, cursor INTEGER DEFAULT 0,
                                seen INTEGER DEFAULT 0);
        ''')

    def add_block(self, raw):
        block = decode_block(raw)
        if block.order <= self.previous_order:
            raise ValueError('Block reading order is not strictly increasing')
        self.previous_order = block.order
        self.db.execute('INSERT INTO blocks VALUES (?,?,?,?,?,?)',
                        (block.id, block.order, block.kind.value, block.table_id, block.section_id,
                         json.dumps(raw, ensure_ascii=False)))
        if block.kind != BlockKind.TABLE:
            self._source(_key('block', block.id), block.text)
            self.readable = self.readable or bool(block.text.strip())

    def add_table(self, raw):
        table = decode_table(raw)
        self.db.execute('INSERT INTO tables VALUES (?,?)', (table.id, json.dumps(raw, ensure_ascii=False)))
        for cell in table.cells:
            self._source(_key('cell', table.id, cell.row, cell.column), cell.text)
            self.readable = self.readable or bool(cell.text.strip())
        if table.caption:
            self._source(_key('caption', table.id), table.caption)
            self.readable = self.readable or bool(table.caption.strip())
        for row in range(table.row_count):
            self._source(_key('row', table.id, row), '')

    def add_section(self, raw):
        section = DocumentSection(**raw)
        self.db.execute('INSERT INTO sections VALUES (?,?,?,?)',
                        (section.id, section.parent_id, section.level, section.title))

    def _source(self, key, text):
        self.db.execute('INSERT INTO coverage(id,text) VALUES (?,?)', (key, text))

    def validate(self):
        if not self.db.execute('SELECT 1 FROM blocks LIMIT 1').fetchone():
            raise ValueError('Extraction has no content blocks')
        invalid = [
            "SELECT 1 FROM blocks b LEFT JOIN sections s ON s.id=b.section_id WHERE b.section_id IS NOT NULL AND s.id IS NULL",
            "SELECT 1 FROM sections s LEFT JOIN sections p ON p.id=s.parent_id WHERE s.parent_id IS NOT NULL AND (p.id IS NULL OR p.level>=s.level)",
            "SELECT 1 FROM blocks b LEFT JOIN tables t ON t.id=b.table_id WHERE b.kind='table' AND t.id IS NULL",
            "SELECT 1 FROM tables t LEFT JOIN blocks b ON b.table_id=t.id GROUP BY t.id HAVING count(b.id)<>1",
        ]
        if any(self.db.execute(query + ' LIMIT 1').fetchone() for query in invalid):
            raise ValueError('Broken or duplicate table/section references')
        if not self.readable:
            raise ValueError('Extraction contains no readable text')
        self.db.commit()

    def blocks(self):
        for row in self.db.execute('SELECT payload FROM blocks ORDER BY ordinal'):
            yield decode_block(json.loads(row[0]))

    def sections(self):
        return self.db.execute('SELECT id,parent_id,level,title FROM sections ORDER BY rowid').fetchall()

    def table(self, table_id):
        row = self.db.execute('SELECT payload FROM tables WHERE id=?', (table_id,)).fetchone()
        if row is None:
            raise ValueError('Unknown table ID')
        return decode_table(json.loads(row[0]))

    def section_context(self, section_id, level):
        path = []
        while section_id is not None:
            row = self.db.execute('SELECT id,parent_id,level,title FROM sections WHERE id=?', (section_id,)).fetchone()
            if row is None:
                raise ValueError('Unknown section ID')
            path.append(row)
            section_id = row[1]
        path.reverse()
        if level is not None and path:
            candidates = [i for i, item in enumerate(path) if item[2] <= level]
            path = path[:(candidates[-1] if candidates else 0) + 1]
        return (path[-1][0] if path else None, tuple(item[3] for item in path))

    def _record(self, key, start, end, text):
        row = self.db.execute('SELECT cursor,seen,length(text),substr(text,?,?) FROM coverage WHERE id=?',
                              (start + 1, end - start, key)).fetchone()
        if (row is None or start < 0 or end < start or row[0] != start or end > row[2]
                or row[3] != text or (row[1] and start == end)):
            raise ValueError('Coverage gap, duplicate, reordered or modified source slice')
        self.db.execute('UPDATE coverage SET cursor=?,seen=1 WHERE id=?', (end, key))

    def record_text(self, block_id, start, end, text):
        self._record(_key('block', block_id), start, end, text)

    def record_cell(self, table_id, row, column, start, end, text):
        self._record(_key('cell', table_id, row, column), start, end, text)

    def record_rows(self, table_id, start, end):
        for row in range(start, end):
            self._record(_key('row', table_id, row), 0, 0, '')

    def record_caption(self, table_id, start, end, text):
        self._record(_key('caption', table_id), start, end, text)

    def finish_coverage(self):
        if self.db.execute('SELECT 1 FROM coverage WHERE seen=0 OR cursor<>length(text) LIMIT 1').fetchone():
            raise ValueError('Chunking did not cover every source text/cell/row')


class SqliteDocumentReader:
    def __init__(self, *, max_item_chars=64 * 1024 * 1024):
        self.max_item_chars = max_item_chars

    @contextmanager
    def open(self, path: Path):
        with tempfile.TemporaryDirectory(prefix='phantom-chunk-index-') as directory:
            # The async persistence adapter serializes iterator advances in worker
            # threads; no concurrent operations use this connection.
            db = sqlite3.connect(str(Path(directory) / 'document.sqlite'), check_same_thread=False)
            try:
                index = IndexedDocument(db)
                with path.open(encoding='utf-8-sig') as stream:
                    fields = {key: value for kind, key, value in JsonObjectItems(
                        stream, max_item_chars=self.max_item_chars, arrays=(),
                        fields={'schema_version', 'document_id', 'title'}).items() if kind == 'field'}
                title = fields.get('title')
                index.title = title.strip() if isinstance(title, str) and title.strip() else None
                version = fields.get('schema_version', 1)
                if type(version) is not int or version not in {1, 2}:
                    raise ValueError('Unsupported extraction schema version')
                if version == 2:
                    if not isinstance(fields.get('document_id'), str) or not fields['document_id']:
                        raise ValueError('V2 extraction requires document_id')
                    arrays = set()
                    with path.open(encoding='utf-8-sig') as stream:
                        for kind, key, value in JsonObjectItems(stream, max_item_chars=self.max_item_chars).items():
                            if kind == 'array':
                                arrays.add(key)
                            elif kind == 'item':
                                {'blocks': index.add_block, 'tables': index.add_table, 'sections': index.add_section}[key](value)
                    if 'blocks' not in arrays:
                        raise ValueError('V2 extraction requires a blocks array')
                else:
                    # Legacy artifacts did not have an incremental wire contract.
                    from .legacy_document import load_legacy
                    with path.open(encoding='utf-8-sig') as stream:
                        load_legacy(json.load(stream), index)
                index.validate()
                yield index
            except sqlite3.IntegrityError as error:
                raise ValueError('Duplicate source identity in extraction') from error
            finally:
                db.close()
