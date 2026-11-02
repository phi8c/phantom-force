from dataclasses import asdict
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from uuid import uuid4

from shared.ingestion.document import (
    BlockKind, ContentBlock, DocumentSection, ExtractedDocumentV2, ExtractedTable,
    ExtractionMetadata, SourceLocation, StructureQuality, TableCell,
)
from module.ingest.chunking.domain.contracts.chunking_engine import ExtractedDocument
from module.ingest.chunking.infrastructure.engine.streaming_chunking_engine import StreamingChunkingEngine
from module.ingest.chunking.infrastructure.reading.indexed_reader import SqliteDocumentReader
from module.ingest.chunking.infrastructure.reading.json_items import JsonObjectItems
from module.ingest.chunking.application.services.chunk_budget import ChunkBudget


class StreamingChunkingTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.path = Path(self.temporary.name) / 'extracted.json'
        self.source = SourceLocation(native_block_index=0, part_id='p1')

    def tearDown(self):
        self.temporary.cleanup()

    def write(self, blocks, tables=(), sections=()):
        document = ExtractedDocumentV2('doc', 'Title', ExtractionMetadata('test', '1', StructureQuality.FLAT),
                                        tuple(blocks), tuple(tables), tuple(sections))
        self.path.write_text(json.dumps(asdict(document), ensure_ascii=False), encoding='utf-8')

    def text(self, text, index=0, section=None, kind=BlockKind.PARAGRAPH):
        return ContentBlock(f'b{index}', index, kind, self.source, text=text, section_id=section)

    def run_engine(self, **options):
        return list(StreamingChunkingEngine(**options).chunk(ExtractedDocument(uuid4(), self.path)))

    def test_flat_text_chunks_without_requested_heading_level(self):
        self.write([self.text('Text without headings. ' * 100)])
        chunks = self.run_engine(level=9, max_chunk_tokens=900)
        self.assertGreater(len(chunks), 1)
        self.assertEqual(''.join(chunk.content for chunk in chunks), 'Text without headings. ' * 100)
        self.assertEqual([chunk.index for chunk in chunks], list(range(len(chunks))))

    def test_unicode_offsets_and_actual_payload_budget(self):
        text = 'Điện áp 220 V. Thiết bị ⚡ sử dụng trong nhà máy.\n' * 80
        self.write([self.text(text)])
        chunks = self.run_engine(max_chunk_tokens=1100)
        budget = ChunkBudget(1100)
        restored = ''
        cursor = 0
        for chunk in chunks:
            self.assertTrue(budget.fits(chunk.content, chunk.metadata))
            span = chunk.metadata['text_spans'][0]
            self.assertEqual(span['start'], cursor)
            restored += chunk.content[span['content_start']:span['content_end']]
            cursor = span['end']
        self.assertEqual(restored, text)

    def test_parent_text_and_children_are_both_preserved(self):
        sections = [DocumentSection('s1', 'Parent', 1), DocumentSection('s2', 'Child', 2, 's1')]
        self.write([self.text('Parent heading', 0, 's1', BlockKind.HEADING),
                    self.text('Parent own content', 1, 's1'),
                    self.text('Child heading', 2, 's2', BlockKind.HEADING),
                    self.text('Child content', 3, 's2')], sections=sections)
        chunks = self.run_engine(max_chunk_tokens=2500)
        joined = '\n'.join(chunk.content for chunk in chunks)
        self.assertIn('Parent own content', joined)
        self.assertIn('Child content', joined)

    def table_document(self, rows=16, large_cell=None, caption=None):
        cells = [TableCell(0, 0, 'Thiết bị', is_header=True), TableCell(0, 1, 'Điện áp', is_header=True)]
        for row in range(1, rows):
            cells.extend([TableCell(row, 0, large_cell if large_cell is not None and row == 1 else f'Device {row}'),
                          TableCell(row, 1, f'{220 + row} V')])
        table = ExtractedTable('t1', rows, 2, tuple(cells), self.source, caption=caption, header_rows=(0,))
        self.write([ContentBlock('tb', 0, BlockKind.TABLE, self.source, table_id='t1')], [table])
        return table

    def test_table_rows_split_and_headers_repeat(self):
        self.table_document()
        chunks = self.run_engine(max_chunk_tokens=1800)
        self.assertGreater(len(chunks), 1)
        ranges = []
        for chunk in chunks:
            payload = json.loads(chunk.content)
            self.assertEqual([cell['text'] for cell in payload['headers']], ['Thiết bị', 'Điện áp'])
            ranges.extend(range(*payload['row_range']))
        self.assertEqual(ranges, list(range(16)))

    def test_oversized_cell_is_fragmented_without_data_loss(self):
        text = 'A very long specification. ' * 150
        self.table_document(rows=2, large_cell=text)
        chunks = self.run_engine(max_chunk_tokens=1200)
        fragments = [json.loads(chunk.content)['cell_fragment'] for chunk in chunks
                     if 'cell_fragment' in json.loads(chunk.content)]
        selected = [fragment for fragment in fragments if fragment['row'] == 1 and fragment['column'] == 0]
        self.assertGreater(len(selected), 1)
        self.assertEqual(''.join(fragment['text'] for fragment in selected), text)
        budget = ChunkBudget(1200)
        self.assertTrue(all(budget.fits(chunk.content, chunk.metadata) for chunk in chunks))

    def test_long_header_and_caption_are_preserved_as_source_fragments(self):
        caption = 'Thông số kỹ thuật. ' * 100
        table = ExtractedTable('t1', 2, 1, (TableCell(0, 0, 'Long header ' * 150, is_header=True),
                               TableCell(1, 0, 'Data')), self.source, caption=caption, header_rows=(0,))
        self.write([ContentBlock('tb', 0, BlockKind.TABLE, self.source, table_id='t1')], [table])
        chunks = self.run_engine(max_chunk_tokens=1100)
        payloads = [json.loads(chunk.content) for chunk in chunks]
        self.assertEqual(''.join(value['caption_fragment']['text'] for value in payloads if 'caption_fragment' in value), caption)
        self.assertTrue(any(value.get('header_reference_only') for value in payloads))

    def test_merged_cell_context_survives_row_boundaries(self):
        cells = [TableCell(0, 0, 'Header', column_span=2, is_header=True),
                 TableCell(1, 0, 'Common device', row_span=6)]
        cells.extend(TableCell(row, 1, 'Specification ' * 8) for row in range(1, 7))
        table = ExtractedTable('t1', 7, 2, tuple(cells), self.source, header_rows=(0,))
        self.write([ContentBlock('tb', 0, BlockKind.TABLE, self.source, table_id='t1')], [table])
        payloads = [json.loads(chunk.content) for chunk in self.run_engine(max_chunk_tokens=1000)]
        self.assertTrue(any(value.get('carry_cells') for value in payloads))

    def test_legacy_parent_table_and_child_content_are_not_dropped(self):
        self.path.write_text(json.dumps({'sections': [{'title': 'Parent', 'level': 1,
            'content': 'Own parent text', 'tables': [{'content': '| A | 220 V |'}],
            'children': [{'title': 'Child', 'level': 2, 'content': 'Child text'}]}]}))
        chunks = self.run_engine(max_chunk_tokens=2500)
        text = '\n'.join(chunk.content for chunk in chunks)
        self.assertIn('Own parent text', text)
        self.assertIn('220 V', text)
        self.assertIn('Child text', text)

    def test_v2_never_calls_json_load_for_entire_document(self):
        self.write([self.text('Preserved text')])
        with patch('json.load', side_effect=AssertionError('Full load forbidden')):
            self.assertTrue(self.run_engine())

    def test_coverage_rejects_missing_duplicate_and_modified_slices(self):
        self.write([self.text('Original')])
        with SqliteDocumentReader().open(self.path) as source:
            with self.assertRaises(ValueError):
                source.finish_coverage()
            with self.assertRaises(ValueError):
                source.record_text('b0', 0, 8, 'Modified')
            source.record_text('b0', 0, 8, 'Original')
            with self.assertRaises(ValueError):
                source.record_text('b0', 0, 8, 'Original')
            source.finish_coverage()

    def test_invalid_wire_inputs_fail(self):
        for payload in ['{"schema_version":3}', '{"schema_version":2,"blocks":[]}',
                        '{"schema_version":2,"schema_version":2}', '{"sections":[]} trailing',
                        '{"blocks":[{"id":"broken"}]}']:
            self.path.write_text(payload)
            with self.subTest(payload=payload), self.assertRaises((ValueError, KeyError, TypeError)):
                self.run_engine()

    def test_incremental_parser_handles_small_reads_and_unknown_large_arrays(self):
        class TinyReader(io.StringIO):
            def read(self, size=-1):
                return super().read(min(size, 7))
        wire = json.dumps({'unknown': [{'text': 'skip me'}] * 50,
                           'schema_version': 2, 'document_id': 'doc',
                           'blocks': [{'order': 123456789, 'text': 'Unicode ⚡'}]})
        items = list(JsonObjectItems(TinyReader(wire)).items())
        self.assertIn(('field', 'schema_version', 2), items)
        self.assertIn(('item', 'blocks', {'order': 123456789, 'text': 'Unicode ⚡'}), items)

    def test_too_small_budget_fails_instead_of_dropping_text(self):
        self.write([self.text('Important')])
        with self.assertRaisesRegex(ValueError, 'budget'):
            self.run_engine(max_chunk_tokens=100)


if __name__ == '__main__':
    unittest.main()
