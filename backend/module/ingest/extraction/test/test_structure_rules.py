import json
import os
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock
from uuid import uuid4
from zipfile import ZipFile

from shared.ingestion.document import BlockKind, SourceLocation
from shared.ingestion.parts import ExtractionManifest, ExtractionPart, PartStatus
from module.ingest.chunking.domain.contracts.chunking_engine import ExtractedDocument
from module.ingest.chunking.infrastructure.engine.streaming_chunking_engine import StreamingChunkingEngine
from module.ingest.extraction.infrastructure.multipart.assembler import assemble
from module.ingest.extraction.infrastructure.multipart.engine import MultipartExtractionEngine
from module.ingest.extraction.infrastructure.multipart.checkpoints import atomic_json, checksum
from module.ingest.extraction.infrastructure.normalization.document_builder import (
    NormalizedDocumentBuilder, serialize_document)
from module.ingest.extraction.infrastructure.normalization.document_codec import decode_document
from module.ingest.extraction.infrastructure.normalization.native_docx import NativeDocxReader
from module.ingest.extraction.infrastructure.normalization.structure_rules import (
    APPLIED_WARNING, ARTICLE, CHAPTER, DECIMAL_BASE, ENV_FLAG, resolve_levels)

SOURCE = SourceLocation(page_number=1)


def resolve(*items):
    """items are text or (text, provider_level)."""
    pairs = [item if isinstance(item, tuple) else (item, None) for item in items]
    return resolve_levels([text for text, _ in pairs], [level for _, level in pairs])


class StructureRulesTests(unittest.TestCase):
    def test_law_labels_come_from_plain_paragraphs(self):
        result = resolve('NGHỊ ĐỊNH', 'Chương I', 'QUY ĐỊNH CHUNG', 'Điều 1. Phạm vi điều chỉnh',
                         'Nghị định này quy định chi tiết.', 'Điều 2. Đối tượng áp dụng', 'Nội dung.',
                         'Chương II', 'QUẢN LÝ NHÀ NƯỚC', 'Điều 3. Trách nhiệm')
        self.assertEqual(result.levels, [None, CHAPTER, None, ARTICLE, None, ARTICLE, None, CHAPTER, None, ARTICLE])
        self.assertEqual(result.titles, {1: 'QUY ĐỊNH CHUNG', 7: 'QUẢN LÝ NHÀ NƯỚC'})

    def test_flat_provider_levels_are_separated(self):
        # Azure marks every heading level 1.
        result = resolve(('Chương I', 1), ('QUY ĐỊNH CHUNG', 1), ('Điều 1. Phạm vi', 1), 'Nội dung',
                         ('Điều 2. Đối tượng', 1))
        self.assertEqual(result.levels, [CHAPTER, None, ARTICLE, None, ARTICLE])

    def test_missing_headings_are_recovered_when_provider_saw_only_some(self):
        result = resolve(('Chương I', 1), 'Điều 1. Phạm vi', 'Nội dung', 'Điều 2. Đối tượng')
        self.assertEqual(result.levels, [CHAPTER, ARTICLE, None, ARTICLE])

    def test_provider_levels_already_correct_are_left_alone(self):
        self.assertIsNone(resolve(('Chương I', 1), ('Điều 1. A', 2), 'Nội dung', ('Điều 2. B', 2), ('Chương II', 1)))

    def test_references_are_not_headings(self):
        result = resolve('Điều 1. A', 'Điều 2. B', 'Điều 5 của Luật này quy định về thuế.',
                         'Điều 3, 4 và 5 được sửa đổi.', 'Điều 3. C')
        self.assertEqual(result.levels, [ARTICLE, ARTICLE, None, None, ARTICLE])

    def test_numbering_must_continue(self):
        result = resolve('Điều 1. A', 'Điều 2. B', 'Điều 3. C', 'Điều 1 Luật Doanh nghiệp', 'Điều 4. D')
        self.assertEqual(result.levels[3], None)
        self.assertEqual(result.levels[4], ARTICLE)

    def test_clauses_inside_an_article_stay_body_text(self):
        result = resolve('Điều 1. Giải thích', '1. Hợp đồng này', '2. Bên A', 'Điều 2. Phạm vi', '1. Quyền', 'Điều 3. C')
        self.assertEqual(result.levels, [ARTICLE, None, None, ARTICLE, None, ARTICLE])

    def test_decimal_outline(self):
        result = resolve('1. MỤC ĐÍCH', 'Nội dung', '2. PHẠM VI', '2.1 Đối tượng', '2.2 Thời gian', '3. TRÁCH NHIỆM')
        self.assertEqual(result.levels, [DECIMAL_BASE + 5, None, DECIMAL_BASE + 5,
                                         DECIMAL_BASE + 10, DECIMAL_BASE + 10, DECIMAL_BASE + 5])

    def test_roman_outline_needs_supporting_evidence(self):
        result = resolve('I. TÌNH HÌNH CHUNG', 'Nội dung', 'II. KẾT QUẢ', 'Nội dung', 'III. PHƯƠNG HƯỚNG')
        self.assertEqual(result.levels, [CHAPTER, None, CHAPTER, None, CHAPTER])
        self.assertIsNone(resolve('I. Tình hình chung', 'II. Kết quả'))

    def test_ordinary_text_is_not_mistaken_for_labels(self):
        for text in ('Mục lục', 'Chương trình đào tạo', 'Điều kiện thanh toán', 'Phần mềm quản lý',
                     '5 kW motor', '1) Bên A cam kết', '15.5 triệu đồng mỗi tháng', 'Điều khoản chung'):
            self.assertIsNone(resolve(text, 'Chương I', 'Chương II') and
                              resolve(text, 'Chương I', 'Chương II').levels[0], text)

    def test_table_of_contents_lines_are_skipped(self):
        result = resolve('Điều 1. Phạm vi ........ 3', 'Điều 2. Đối tượng ........ 4', 'Chương I', 'Điều 1. Phạm vi', 'Điều 2. B')
        self.assertEqual(result.levels[:2], [None, None])
        self.assertEqual(result.levels[2:], [CHAPTER, ARTICLE, ARTICLE])

    def test_decomposed_unicode_is_recognised(self):
        import unicodedata
        nfd = lambda text: unicodedata.normalize('NFD', text)
        result = resolve(nfd('Chương I'), nfd('Điều 1. Phạm vi'), nfd('Điều 2. Đối tượng'))
        self.assertEqual(result.levels, [CHAPTER, ARTICLE, ARTICLE])

    def test_unlabeled_provider_headings_become_text_when_labels_decide(self):
        # An extra level would push every Điều down and break the configured chunk level.
        result = resolve(('CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM', 1), 'Điều 1. A', ('Quyền của bên A', 2), 'Điều 2. B')
        self.assertEqual(result.levels, [None, ARTICLE, None, ARTICLE])

    def test_typed_table_of_contents_is_not_promoted(self):
        contents = ['MỤC LỤC', '1. Giới thiệu', '1.1. Mục tiêu', '2. Phạm vi', '2.1. Đối tượng']
        body = [('1. Giới thiệu', 1), 'Nội dung', ('1.1. Mục tiêu', 2), 'Nội dung', ('2. Phạm vi', 1), 'Nội dung',
                ('2.1. Đối tượng', 2), 'Nội dung']
        self.assertIsNone(resolve(*contents, *body))  # provider levels are right; the contents must not break them
        flat = resolve(*contents, '1. GIỚI THIỆU', 'Nội dung', '1.1. Mục tiêu', 'Nội dung', '2. PHẠM VI', 'Nội dung',
                       '2.1. Đối tượng')
        self.assertEqual(flat.levels[:5], [None] * 5)
        self.assertEqual([level is not None for level in flat.levels[5:]], [True, False, True, False, True, False, True])

    def test_numbered_list_items_are_not_headings(self):
        result = resolve('1. GIỚI THIỆU', 'Nội dung', '1. Bấm nút Thêm', '2. Chọn mô hình', '3. Gõ câu hỏi',
                         '2. PHẠM VI', 'Nội dung', '3. KẾT LUẬN')
        self.assertEqual(result.levels, [DECIMAL_BASE + 5, None, None, None, None, DECIMAL_BASE + 5, None, DECIMAL_BASE + 5])

    def test_sound_provider_markup_is_never_overridden(self):
        # Even when one sub-heading sits a level deeper than its siblings (as in real Word files).
        self.assertIsNone(resolve(('1. A', 1), ('1.1 B', 2), ('1.2 C', 2), ('2. D', 1), ('2.1 E', 3), ('2.2 F', 2),
                                  'Bấm nút', ('3. G', 1), ('3.1 H', 2)))
        self.assertIsNone(resolve(('Giới thiệu', 1), ('Phạm vi', 2), ('Mục đích', 2), ('Kết luận', 1), ('Phụ lục', 1),
                                  '1. Bấm nút', '2. Chọn', '3. Gõ'))

    def test_weak_evidence_changes_nothing(self):
        self.assertIsNone(resolve('Điều 1. Duy nhất', 'Nội dung'))
        self.assertIsNone(resolve('Nội dung', 'Không có nhãn nào', ('Tiêu đề', 1)))

    def test_appendix_and_english_labels(self):
        result = resolve('Article 1. Definitions', 'Article 2. Term', 'PHỤ LỤC I', 'Phụ lục 2', 'Article 3. Fees')
        self.assertEqual(result.levels, [ARTICLE, ARTICLE, CHAPTER, CHAPTER, ARTICLE])

    def test_resolution_is_fast_on_large_documents(self):
        texts = []
        for chapter in range(1, 201):
            texts += [f'Chương {chapter}', 'TÊN CHƯƠNG']
            for article in range(1, 26):
                texts += [f'Điều {article}. Tên điều', 'Nội dung ' * 40]
        started = time.perf_counter()
        result = resolve_levels(texts, [None] * len(texts))
        elapsed = time.perf_counter() - started
        self.assertEqual(len(result.levels), len(texts))
        self.assertLess(elapsed, 1.0, f'{len(texts)} paragraphs took {elapsed:.3f}s')


class BuilderIntegrationTests(unittest.TestCase):
    def build(self, rules):
        builder = NormalizedDocumentBuilder('doc', 'Title', 'fake', '1', structure_rules=rules)
        for text in ('NGHỊ ĐỊNH', 'Chương I', 'QUY ĐỊNH CHUNG', 'Điều 1. Phạm vi', 'Nội dung A', 'Điều 2. Đối tượng'):
            builder.add_text(text, SOURCE)
        return builder.build()

    def test_rules_off_keeps_flat_document(self):
        result = self.build(False)
        self.assertEqual(result.sections, ())
        self.assertNotIn(APPLIED_WARNING, result.extraction.warnings)

    def test_rules_on_builds_nested_sections_without_changing_text(self):
        result = self.build(True)
        self.assertEqual([block.text for block in result.blocks], [block.text for block in self.build(False).blocks])
        self.assertEqual([(s.title, s.level) for s in result.sections],
                         [('Chương I - QUY ĐỊNH CHUNG', CHAPTER), ('Điều 1. Phạm vi', ARTICLE),
                          ('Điều 2. Đối tượng', ARTICLE)])
        self.assertEqual(result.sections[1].parent_id, result.sections[0].id)
        self.assertEqual(result.sections[2].parent_id, result.sections[0].id)
        self.assertIn(APPLIED_WARNING, result.extraction.warnings)
        self.assertEqual([block.kind for block in result.blocks].count(BlockKind.HEADING), 3)

    def test_documents_without_labels_are_identical_with_rules_on(self):
        def run(rules):
            builder = NormalizedDocumentBuilder('doc', 'Title', 'fake', '1', structure_rules=rules)
            builder.add_text('Giới thiệu', SOURCE, level=1)
            builder.add_text('Nội dung', SOURCE)
            builder.add_text('Chi tiết', SOURCE, level=2)
            return serialize_document(builder.build())
        self.assertEqual(run(True), run(False))

    def test_tables_keep_reading_order(self):
        from shared.ingestion.document import ExtractedTable, TableCell
        builder = NormalizedDocumentBuilder('doc', 'Title', 'fake', '1', structure_rules=True)
        builder.add_text('Điều 1. A', SOURCE)
        builder.add_table(ExtractedTable('t0', 1, 1, (TableCell(0, 0, 'x'),), SOURCE))
        builder.add_text('Điều 2. B', SOURCE)
        result = builder.build()
        self.assertEqual([block.kind for block in result.blocks],
                         [BlockKind.HEADING, BlockKind.TABLE, BlockKind.HEADING])
        self.assertEqual(result.blocks[1].section_id, result.sections[0].id)

    def test_docx_with_typed_labels_gets_sections_when_enabled(self):
        paragraphs = ''.join(f'<w:p><w:r><w:t>{text}</w:t></w:r></w:p>' for text in (
            'Chương I', 'QUY ĐỊNH CHUNG', 'Điều 1. Phạm vi', 'Nội dung', 'Điều 2. Đối tượng', 'Nội dung'))
        xml = ('<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body>'
               + paragraphs + '</w:body></w:document>')
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'law.docx'
            with ZipFile(path, 'w') as archive:
                archive.writestr('word/document.xml', xml)
            with mock.patch.dict(os.environ, {ENV_FLAG: '0'}):
                self.assertEqual(NativeDocxReader().read(path).sections, ())
            with mock.patch.dict(os.environ, {ENV_FLAG: '1'}):
                result = NativeDocxReader().read(path)
        self.assertEqual([s.level for s in result.sections], [CHAPTER, ARTICLE, ARTICLE])


    def test_styled_docx_with_typed_contents_and_step_lists_is_unchanged(self):
        # Shape of a real user guide: Heading styles, a hand-typed contents page and numbered steps.
        def paragraph(text, style=None):
            props = f'<w:pPr><w:pStyle w:val="{style}"/></w:pPr>' if style else ''
            return f'<w:p>{props}<w:r><w:t>{text}</w:t></w:r></w:p>'
        body = ''.join([
            paragraph('MỤC LỤC'), paragraph('1. Giao diện'), paragraph('1.1. Đăng nhập'), paragraph('2. Tổng quan'),
            paragraph('2.1. Việc cần xử lý'), paragraph('3. Trợ lý AI'),
            paragraph('1. Giao diện', 'Heading1'), paragraph('Nội dung chung.'),
            paragraph('1.1. Đăng nhập', 'Heading2'), paragraph('Mở trình duyệt.'),
            paragraph('2. Tổng quan', 'Heading1'), paragraph('Nội dung.'),
            paragraph('2.1. Việc cần xử lý', 'Heading2'), paragraph('Danh sách việc.'),
            paragraph('3. Trợ lý AI', 'Heading1'), paragraph('1. Bấm Trò chuyện mới'), paragraph('2. Chọn mô hình'),
            paragraph('3. Gõ câu hỏi'), paragraph('4. Kết thúc', 'Heading1')])
        styles = ('<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
                  '<w:style w:styleId="Heading1"><w:name w:val="heading 1"/></w:style>'
                  '<w:style w:styleId="Heading2"><w:name w:val="heading 2"/></w:style></w:styles>')
        document = ('<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body>'
                    + body + '</w:body></w:document>')
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'guide.docx'
            with ZipFile(path, 'w') as archive:
                archive.writestr('word/document.xml', document)
                archive.writestr('word/styles.xml', styles)
            results = {}
            for flag in ('0', '1'):
                with mock.patch.dict(os.environ, {ENV_FLAG: flag}):
                    result = NativeDocxReader().read(path)
                results[flag] = ([(s.title, s.level) for s in result.sections],
                                 [(b.kind, b.text) for b in result.blocks], result.extraction.warnings)
        self.assertEqual(results['0'][0], results['1'][0])
        self.assertEqual(results['0'][1], results['1'][1])
        self.assertEqual(len(results['1'][0]), 6)
        self.assertNotIn(APPLIED_WARNING, results['1'][2])


class AssemblerCompactionTests(unittest.TestCase):
    def assemble(self, parts):
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            records = []
            for index, texts in enumerate(parts):
                builder = NormalizedDocumentBuilder('doc', 'Title', 'fake', '1', structure_rules=True)
                for text in texts:
                    builder.add_text(text, SourceLocation(page_number=1))
                artifact = directory / f'p{index}.json'
                atomic_json(artifact, serialize_document(builder.build()))
                records.append(ExtractionPart(f'p{index}', index, PartStatus.COMPLETED, index + 1, index + 1,
                                              artifact.name, checksum(artifact)))
            manifest = ExtractionManifest('doc', 'hash', 'config', 'page', tuple(records))
            _, output = assemble(directory, manifest, 'fake')
            payload = json.loads(output.read_text(encoding='utf-8'))
            decode_document(payload)
            return payload

    def test_levels_are_compacted_and_hierarchy_spans_parts(self):
        payload = self.assemble([['Chương I', 'Điều 1. A', 'Nội dung', 'Điều 2. B'],
                                 ['Điều 3. C', 'Nội dung', 'Điều 4. D']])
        sections = payload['sections']
        self.assertEqual([s['level'] for s in sections], [1, 2, 2, 2, 2])
        chapter = sections[0]['id']
        self.assertTrue(all(s['parent_id'] == chapter for s in sections[1:]))
        self.assertIn(APPLIED_WARNING, payload['extraction']['warnings'])

    def test_decimal_only_document_compacts_to_one_two(self):
        payload = self.assemble([['1. MỤC ĐÍCH', '1.1 Phạm vi', '2. TRÁCH NHIỆM']])
        self.assertEqual([s['level'] for s in payload['sections']], [1, 2, 1])


class ExtractionToChunkingWithRulesTests(unittest.IsolatedAsyncioTestCase):
    LINES = ('NGHỊ ĐỊNH', 'Chương I', 'QUY ĐỊNH CHUNG', 'Điều 1. Phạm vi điều chỉnh', 'Nghị định này quy định về thuế.',
             'Điều 2. Đối tượng áp dụng', 'Áp dụng cho mọi tổ chức.', 'Điều 3. Giải thích từ ngữ',
             '1. Thuế là khoản thu.', '2. Phí là khoản thu khác.', 'Chương II', 'QUẢN LÝ NHÀ NƯỚC',
             'Điều 4. Trách nhiệm', 'Bộ Tài chính chịu trách nhiệm.', 'Điều 5. Kiểm tra', 'Theo Điều 4 của Nghị định này.')

    async def chunk_paths(self, rules):
        xml = ('<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body>'
               + ''.join(f'<w:p><w:r><w:t>{text}</w:t></w:r></w:p>' for text in self.LINES) + '</w:body></w:document>')
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / 'law.docx'
            with ZipFile(source, 'w') as archive:
                archive.writestr('word/document.xml', xml)
            # Five blocks per part forces Chương/Điều context to survive part boundaries.
            engine = MultipartExtractionEngine('docling', {'extraction_runtime': {
                'docx_blocks_per_part': 5, 'structure_rules': rules}}, cache_root=root / 'cache')
            result = await engine.extract(source)
            return [(chunk.metadata['heading_path'], chunk.content) for chunk in
                    StreamingChunkingEngine().chunk(ExtractedDocument(uuid4(), result.content_file))]

    async def test_typed_labels_become_heading_paths_across_parts(self):
        before = await self.chunk_paths(False)
        self.assertTrue(all(path == [] for path, _ in before))
        after = await self.chunk_paths(True)
        paths = [path for path, _ in after]
        self.assertIn(['Chương I - QUY ĐỊNH CHUNG', 'Điều 3. Giải thích từ ngữ'], paths)
        self.assertIn(['Chương II - QUẢN LÝ NHÀ NƯỚC', 'Điều 5. Kiểm tra'], paths)
        # Clauses and a citation stay inside their Điều, and no source text is lost or duplicated.
        article_three = next(content for path, content in after if path[-1:] == ['Điều 3. Giải thích từ ngữ'])
        self.assertIn('1. Thuế là khoản thu.', article_three)
        self.assertEqual(' '.join(content for _, content in after).count('Theo Điều 4 của Nghị định này.'), 1)
        self.assertEqual(sorted(' '.join(c for _, c in before).split()), sorted(' '.join(c for _, c in after).split()))


if __name__ == '__main__':
    unittest.main()
