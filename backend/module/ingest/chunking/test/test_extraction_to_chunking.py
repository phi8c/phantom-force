import json
from pathlib import Path
import tempfile
import unittest
from uuid import uuid4
from zipfile import ZipFile

from module.ingest.extraction.infrastructure.multipart.engine import MultipartExtractionEngine
from module.ingest.chunking.domain.contracts.chunking_engine import ExtractedDocument
from module.ingest.chunking.infrastructure.engine.streaming_chunking_engine import StreamingChunkingEngine
from module.ingest.chunking.application.services.chunk_budget import ChunkBudget


class ExtractionToChunkingTests(unittest.IsolatedAsyncioTestCase):
    async def test_real_docx_parts_feed_streaming_chunker(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / 'source.docx'
            with ZipFile(source, 'w') as archive:
                archive.writestr('word/document.xml', '''
                <w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body>
                  <w:p><w:r><w:t>Intro before heading</w:t></w:r></w:p>
                  <w:p><w:pPr><w:outlineLvl w:val="0"/></w:pPr><w:r><w:t>Specifications</w:t></w:r></w:p>
                  <w:tbl><w:tr><w:trPr><w:tblHeader/></w:trPr>
                    <w:tc><w:p><w:r><w:t>Device</w:t></w:r></w:p></w:tc>
                    <w:tc><w:p><w:r><w:t>Voltage</w:t></w:r></w:p></w:tc></w:tr>
                    <w:tr><w:tc><w:p><w:r><w:t>A</w:t></w:r></w:p></w:tc>
                    <w:tc><w:p><w:r><w:t>220 V</w:t></w:r></w:p></w:tc></w:tr>
                  </w:tbl>
                  <w:p><w:r><w:t>Text after the table</w:t></w:r></w:p>
                </w:body></w:document>''')
            extraction = MultipartExtractionEngine('docling',
                {'extraction_runtime': {'docx_blocks_per_part': 2}}, cache_root=root / 'cache')
            result = await extraction.extract(source)
            chunks = list(StreamingChunkingEngine().chunk(ExtractedDocument(uuid4(), result.content_file)))
            all_content = '\n'.join(chunk.content for chunk in chunks)
            self.assertIn('Intro before heading', all_content)
            self.assertIn('220 V', all_content)
            self.assertIn('Text after the table', all_content)
            self.assertTrue(all(ChunkBudget().fits(chunk.content, chunk.metadata) for chunk in chunks))
            self.assertTrue(any(chunk.metadata['part_ids'] == ['native_block-2-3'] for chunk in chunks))
