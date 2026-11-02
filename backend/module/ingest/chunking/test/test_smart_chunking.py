from dataclasses import asdict
import json
from pathlib import Path
import tempfile
import unittest
from uuid import uuid4

from shared.ingestion.document import (
    BlockKind, ContentBlock, DocumentSection, ExtractedDocumentV2, ExtractedTable,
    ExtractionMetadata, SourceLocation, StructureQuality, TableCell,
)
from module.ingest.chunking.domain.contracts.chunking_engine import ExtractedDocument
from module.ingest.chunking.infrastructure.engine.chunking_engine_resolver import DbChunkingEngineResolver
from module.ingest.chunking.infrastructure.engine.smart_chunking_engine import SmartChunkingEngine


class WordCounter:
    """One token per word keeps budgets in these tests easy to read."""
    def count(self, text):
        return len(text.split())


def words(count, label='từ'):
    return ' '.join(f'{label}{index}' for index in range(count))


class SmartChunkingTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.path = Path(self.temporary.name) / 'extracted.json'
        self.location = SourceLocation(native_block_index=0)
        self.blocks, self.sections = [], []

    def tearDown(self):
        self.temporary.cleanup()

    def section(self, title, level, parent=None):
        section = DocumentSection(f's{len(self.sections)}', title, level, parent)
        self.sections.append(section)
        self.add(title, section.id, BlockKind.HEADING)
        return section.id

    def add(self, text, section=None, kind=BlockKind.PARAGRAPH):
        index = len(self.blocks)
        self.blocks.append(ContentBlock(f'b{index}', index, kind, self.location, text=text, section_id=section))

    def run_engine(self, tables=(), title='Tài liệu mẫu', **options):
        quality = StructureQuality.STRUCTURED if self.sections else StructureQuality.FLAT
        document = ExtractedDocumentV2('doc', title, ExtractionMetadata('test', '1', quality),
                                       tuple(self.blocks), tuple(tables), tuple(self.sections))
        self.path.write_text(json.dumps(asdict(document), ensure_ascii=False), encoding='utf-8')
        options.setdefault('counter', WordCounter())
        options.setdefault('reserve_tokens', 0)
        return list(SmartChunkingEngine(**options).chunk(ExtractedDocument(uuid4(), self.path)))

    def restored(self, chunks):
        """Source text rebuilt from the recorded spans: nothing lost, nothing repeated."""
        pieces = {}
        for chunk in chunks:
            for span in chunk.metadata.get('text_spans', ()):
                pieces.setdefault(span['block_id'], []).append(chunk.content[span['content_start']:span['content_end']])
        return {block.id: ''.join(pieces[block.id]) for block in self.blocks if block.kind != BlockKind.TABLE}

    def assertTextPreserved(self, chunks):
        self.assertEqual(self.restored(chunks), {b.id: b.text for b in self.blocks if b.kind != BlockKind.TABLE})

    def law(self, articles, article_words=30, chapters=1):
        for chapter in range(1, chapters + 1):
            parent = self.section(f'Chương {chapter}', 1)
            for article in range(1, articles + 1):
                child = self.section(f'Điều {article}. Tên điều', 2, parent)
                self.add(words(article_words, f'c{chapter}d{article}x'), child)

    def test_small_document_stays_in_one_chunk(self):
        self.law(2, 20)
        chunks = self.run_engine(target_tokens=200, max_chunk_tokens=400)
        self.assertEqual(len(chunks), 1)
        self.assertIn('Điều 2.', chunks[0].content)
        self.assertNotIn('context_prefix', chunks[0].metadata)
        self.assertTextPreserved(chunks)

    def test_large_chapter_is_split_by_article_and_keeps_chapter_heading(self):
        self.law(4, 30)
        chunks = self.run_engine(target_tokens=75, max_chunk_tokens=400)
        self.assertEqual(len(chunks), 2)
        second = chunks[1]
        self.assertTrue(second.content.startswith('Chương 1\n\nĐiều 3. Tên điều'))
        self.assertEqual(second.metadata['heading_path'], ['Chương 1'])
        self.assertEqual(second.metadata['context_prefix'], 'Chương 1')
        self.assertIn('Điều 1.', chunks[0].content)
        self.assertTextPreserved(chunks)

    def test_bare_parent_heading_is_not_a_chunk_of_its_own(self):
        self.law(3, 30)  # Chương heading (2) + Điều 1 (33) just overflows a 34-token target
        chunks = self.run_engine(target_tokens=34, max_chunk_tokens=400)
        self.assertNotIn('Chương 1', [chunk.content.strip() for chunk in chunks])
        self.assertTrue(chunks[0].content.startswith('Chương 1\n\nĐiều 1.'))
        self.assertTextPreserved(chunks)

    def test_chunks_never_merge_across_different_parents(self):
        self.law(3, 30, chapters=2)
        chunks = self.run_engine(target_tokens=75, max_chunk_tokens=400)
        for chunk in chunks:
            self.assertFalse('Chương 1' in chunk.content.split('\n\n')[0] and 'c2d1x0' in chunk.content, chunk.content[:80])
        last_of_first = next(c for c in chunks if 'c1d3x0' in c.content)
        self.assertNotIn('c2d1x0', last_of_first.content)
        self.assertTextPreserved(chunks)

    def test_oversized_leaf_is_split_at_blocks_and_each_piece_keeps_its_context(self):
        parent = self.section('Chương 1', 1)
        leaf = self.section('Điều 1. Rất dài', 2, parent)
        for index in range(5):
            self.add(words(50, f'p{index}x'), leaf)
        chunks = self.run_engine(target_tokens=100, max_chunk_tokens=200)
        self.assertGreater(len(chunks), 1)
        counter = WordCounter()
        for chunk in chunks:
            self.assertLessEqual(counter.count(chunk.content), 200)
            self.assertNotEqual(chunk.content.rstrip().splitlines()[-1], 'Điều 1. Rất dài')
        for chunk in chunks[1:]:
            self.assertTrue(chunk.content.startswith('Chương 1 › Điều 1. Rất dài\n\n'), chunk.content[:60])
        self.assertTextPreserved(chunks)

    def test_single_huge_paragraph_is_cut_at_sentence_edges(self):
        parent = self.section('Chương 1', 1)
        leaf = self.section('Điều 1. Một đoạn', 2, parent)
        self.add(' '.join(f'Câu {n} có năm từ.' for n in range(200)), leaf)
        chunks = self.run_engine(target_tokens=100, max_chunk_tokens=200)
        counter = WordCounter()
        self.assertGreater(len(chunks), 3)
        for chunk in chunks:
            self.assertLessEqual(counter.count(chunk.content), 200)
        self.assertTextPreserved(chunks)
        self.assertTrue(all(chunk.content.rstrip().endswith('.') for chunk in chunks))

    def test_document_without_headings_uses_title_and_balanced_packing(self):
        for index in range(20):
            self.add(words(30, f'q{index}x'))
        chunks = self.run_engine(target_tokens=200, max_chunk_tokens=400, title='Quy chế nội bộ')
        counter = WordCounter()
        self.assertGreaterEqual(len(chunks), 3)
        for chunk in chunks:
            self.assertTrue(chunk.content.startswith('Quy chế nội bộ\n\n'))
            self.assertLessEqual(counter.count(chunk.content), 400)
            self.assertEqual(chunk.metadata['heading_path'], [])
        sizes = [counter.count(chunk.content) - 3 for chunk in chunks]
        self.assertLessEqual(max(sizes) - min(sizes), 60, sizes)
        self.assertTextPreserved(chunks)

    def test_text_before_first_heading_gets_the_title(self):
        self.add(words(10, 'pre'))
        self.law(2, 10)
        chunks = self.run_engine(target_tokens=30, max_chunk_tokens=200, title='Nghị định')
        self.assertTrue(chunks[0].content.startswith('Nghị định\n\n'))
        self.assertTextPreserved(chunks)

    def test_heading_context_can_be_disabled(self):
        self.law(4, 30)
        chunks = self.run_engine(target_tokens=75, max_chunk_tokens=400, include_heading_context=False)
        self.assertTrue(all('context_prefix' not in chunk.metadata for chunk in chunks))
        self.assertTrue(chunks[1].content.startswith('Điều 3.'))
        self.assertTextPreserved(chunks)

    def test_tables_are_separate_chunks_with_the_section_path(self):
        parent = self.section('Chương 1', 1)
        leaf = self.section('Điều 1. Có bảng', 2, parent)
        self.add(words(20, 'trước'), leaf)
        self.blocks.append(ContentBlock('tb', len(self.blocks), BlockKind.TABLE, self.location,
                                        table_id='t1', section_id=leaf))
        self.add(words(20, 'sau'), leaf)
        table = ExtractedTable('t1', 2, 2, (TableCell(0, 0, 'Tên', is_header=True), TableCell(0, 1, 'Giá', is_header=True),
                                            TableCell(1, 0, 'A'), TableCell(1, 1, '5')), self.location, header_rows=(0,))
        chunks = self.run_engine(tables=[table], target_tokens=100, max_chunk_tokens=400)
        kinds = ['table' if '"table_id"' in chunk.content else 'text' for chunk in chunks]
        self.assertEqual(kinds, ['text', 'table', 'text'])
        self.assertEqual(chunks[1].metadata['heading_path'], ['Chương 1', 'Điều 1. Có bảng'])
        self.assertEqual([chunk.index for chunk in chunks], [0, 1, 2])
        self.assertTextPreserved(chunks)

    def test_invalid_budget_is_rejected(self):
        self.law(1, 5)
        with self.assertRaises(ValueError):
            self.run_engine(target_tokens=500, max_chunk_tokens=400)

    def test_resolver_builds_smart_engine_with_agreed_defaults(self):
        resolver = DbChunkingEngineResolver(session=None)
        engine = resolver._create_engine(code='smart', configuration={})
        self.assertIsInstance(engine, SmartChunkingEngine)
        self.assertEqual((engine.planner.target, engine.planner.budget.max_tokens), (2000, 4000))
        self.assertEqual(engine.planner.budget.counter.encoding_name, 'cl100k_base')
        tuned = resolver._create_engine(code='SMART', configuration={
            'target_tokens': 1500, 'max_chunk_tokens': 3000, 'include_heading_context': False,
            'chunking_runtime': {'token_counter': 'tiktoken', 'encoding_name': 'o200k_base'}})
        self.assertEqual((tuned.planner.target, tuned.planner.budget.max_tokens, tuned.planner.context),
                         (1500, 3000, False))

    def test_real_tokenizer_keeps_vietnamese_chunks_under_the_cap(self):
        parent = self.section('Chương 1', 1)
        for article in range(1, 41):
            child = self.section(f'Điều {article}. Trách nhiệm quản lý nhà nước', 2, parent)
            self.add(('Bộ Tài chính chịu trách nhiệm hướng dẫn thực hiện các quy định của Nghị định này. ' * 25).strip(), child)
        chunks = SmartChunkingEngine(target_tokens=2000, max_chunk_tokens=4000)
        document = ExtractedDocumentV2('doc', 'Nghị định', ExtractionMetadata('test', '1', StructureQuality.STRUCTURED),
                                       tuple(self.blocks), (), tuple(self.sections))
        self.path.write_text(json.dumps(asdict(document), ensure_ascii=False), encoding='utf-8')
        result = list(chunks.chunk(ExtractedDocument(uuid4(), self.path)))
        counter = chunks.planner.budget.counter
        sizes = [counter.count(chunk.content) for chunk in result]
        self.assertLessEqual(max(sizes), 4000 - 64, sizes)
        self.assertGreater(len(result), 1)
        self.assertTextPreserved(result)


if __name__ == '__main__':
    unittest.main()
