import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace as Obj
from zipfile import ZipFile

from shared.ingestion.document import BlockKind, StructureQuality, SourceLocation
from module.ingest.extraction.infrastructure.normalization.native_docx import NativeDocxReader
from module.ingest.extraction.infrastructure.normalization.document_builder import serialize_document
from module.ingest.extraction.infrastructure.normalization.html_table import HtmlTableReader
from module.ingest.extraction.infrastructure.normalization.provider_documents import normalize_docling, normalize_azure
from module.ingest.extraction.infrastructure.normalization.unstructured_document import normalize_unstructured

PREFIX = '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body>'
SUFFIX = '</w:body></w:document>'


class ExtractionNormalizationTests(unittest.TestCase):
    def read_docx(self, body, styles=None):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'sample.docx'
            with ZipFile(path, 'w') as archive:
                archive.writestr('word/document.xml', PREFIX + body + SUFFIX)
                if styles:
                    archive.writestr('word/styles.xml', styles)
            return NativeDocxReader().read(path)

    def test_flat_docx_keeps_text_and_table_before_heading(self):
        result = self.read_docx('''
          <w:p><w:r><w:t>Text before heading</w:t></w:r></w:p>
          <w:tbl><w:tr><w:tc><w:p><w:r><w:t>220 V</w:t></w:r></w:p></w:tc></w:tr></w:tbl>
          <w:p><w:pPr><w:outlineLvl w:val="0"/></w:pPr><w:r><w:t>Title</w:t></w:r></w:p>
          <w:p><w:r><w:t>After heading</w:t></w:r></w:p>''')
        self.assertEqual([block.kind for block in result.blocks], [
            BlockKind.PARAGRAPH, BlockKind.TABLE, BlockKind.HEADING, BlockKind.PARAGRAPH])
        self.assertEqual(result.blocks[0].text, 'Text before heading')
        self.assertEqual(result.tables[0].cells[0].text, '220 V')
        self.assertEqual(result.extraction.structure_quality, StructureQuality.PARTIAL)

    def test_docx_preserves_horizontal_and_vertical_merge(self):
        result = self.read_docx('''<w:tbl>
          <w:tblGrid><w:gridCol/><w:gridCol/></w:tblGrid>
          <w:tr><w:trPr><w:tblHeader/></w:trPr><w:tc><w:tcPr><w:gridSpan w:val="2"/><w:vMerge w:val="restart"/></w:tcPr><w:p><w:r><w:t>Header</w:t></w:r></w:p></w:tc></w:tr>
          <w:tr><w:tc><w:tcPr><w:gridSpan w:val="2"/><w:vMerge/></w:tcPr><w:p/></w:tc></w:tr>
        </w:tbl>''')
        cell = result.tables[0].cells[0]
        self.assertEqual((cell.row_span, cell.column_span, cell.text), (2, 2, 'Header'))
        self.assertEqual(result.tables[0].header_rows, (0,))
        self.assertEqual(result.extraction.structure_quality, StructureQuality.FLAT)

    def test_docx_custom_heading_style_inherits_outline(self):
        styles = '''<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
          <w:style w:styleId="Base"><w:pPr><w:outlineLvl w:val="1"/></w:pPr></w:style>
          <w:style w:styleId="Custom"><w:basedOn w:val="Base"/></w:style></w:styles>'''
        result = self.read_docx('<w:p><w:pPr><w:pStyle w:val="Custom"/></w:pPr><w:r><w:t>Custom title</w:t></w:r></w:p>', styles)
        self.assertEqual(result.sections[0].level, 2)

    def test_docx_content_controls_and_nested_table_text(self):
        result = self.read_docx('''<w:sdt><w:sdtContent><w:p><w:r><w:t>Wrapped</w:t></w:r></w:p></w:sdtContent></w:sdt>
          <w:tbl><w:tr><w:tc><w:p><w:r><w:t>Outer</w:t></w:r></w:p><w:tbl><w:tr><w:tc><w:p><w:r><w:t>Inner</w:t></w:r></w:p></w:tc></w:tr></w:tbl></w:tc></w:tr></w:tbl>''')
        self.assertEqual(result.blocks[0].text, 'Wrapped')
        self.assertIn('Inner', result.tables[0].cells[0].text)
        self.assertTrue(any('Nested' in warning for warning in result.extraction.warnings))

    def test_empty_docx_fails(self):
        with self.assertRaisesRegex(ValueError, 'no content blocks'):
            self.read_docx('<w:p/>')

    def test_html_spans_and_headers(self):
        table = HtmlTableReader().read('<table><tr><th rowspan="2">A</th><th>B</th></tr><tr><td>C</td></tr></table>', table_id='t', source=SourceLocation())
        self.assertEqual(table.cells[0].row_span, 2)
        self.assertEqual((table.cells[-1].row, table.cells[-1].column), (1, 1))

    def test_docling_keeps_plain_text_and_raw_table_cells(self):
        text = Obj(label='text', text='No heading', prov=[])
        table = Obj(label='table', prov=[], data=Obj(num_rows=1, num_cols=2, table_cells=[
            Obj(start_row_offset_idx=0, start_col_offset_idx=0, text='Merged', row_span=1, col_span=2, column_header=True)]))
        document = Obj(name='PDF', iterate_items=lambda: iter([(text, 0), (table, 0)]))
        result = normalize_docling(document, document_id='doc', version='test')
        self.assertEqual(result.blocks[0].text, 'No heading')
        self.assertEqual(result.tables[0].cells[0].column_span, 2)

    def test_unstructured_table_before_title_and_missing_grid_warning(self):
        elements = [Obj(category='Table', text='A 220', metadata=Obj(text_as_html=None))]
        result = normalize_unstructured(elements, document_id='doc', title='Title', version='test')
        self.assertEqual(result.tables[0].cells[0].text, 'A 220')
        self.assertTrue(result.extraction.warnings)

    def test_azure_preserves_order_and_deduplicates_table_paragraph(self):
        paragraph = Obj(content='Intro', spans=[Obj(offset=0, length=5)], role=None, bounding_regions=[])
        duplicate = Obj(content='A', spans=[Obj(offset=10, length=1)], role=None, bounding_regions=[])
        table = Obj(spans=[Obj(offset=10, length=5)], bounding_regions=[], row_count=1, column_count=1,
                    cells=[Obj(row_index=0, column_index=0, content='A', row_span=1, column_span=1, kind=None)])
        result = normalize_azure(Obj(tables=[table], paragraphs=[duplicate, paragraph]), document_id='doc', title='Title', version='test')
        self.assertEqual(len(result.blocks), 2)
        self.assertEqual(result.blocks[0].text, 'Intro')

    def test_legacy_projection_keeps_all_blocks_and_table_json(self):
        result = self.read_docx('<w:p><w:r><w:t>Intro</w:t></w:r></w:p><w:tbl><w:tr><w:tc><w:p><w:r><w:t>5 kW</w:t></w:r></w:p></w:tc></w:tr></w:tbl>')
        payload = serialize_document(result)
        self.assertEqual(len(payload['legacy_sections']), len(result.blocks))
        table = json.loads(payload['legacy_sections'][1]['content'])
        self.assertEqual(table['cells'][0]['text'], '5 kW')
        self.assertEqual(payload['sections'], ())


if __name__ == '__main__':
    unittest.main()
