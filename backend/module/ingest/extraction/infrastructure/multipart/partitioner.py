"""Partition PDF pages or DOCX body blocks without rendering or OCR."""
from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import ZipFile, ZIP_DEFLATED

from shared.ingestion.parts import ExtractionPart, PartStatus

W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'


class SourcePartitioner:
    def __init__(self, pdf_pages: int = 20, docx_blocks: int = 200):
        if min(pdf_pages, docx_blocks) < 1:
            raise ValueError('Partition sizes must be positive')
        self.pdf_pages = pdf_pages
        self.docx_blocks = docx_blocks

    def plan(self, source: Path, directory: Path) -> tuple[str, tuple[ExtractionPart, ...]]:
        if source.suffix.lower() == '.pdf':
            from pypdf import PdfReader
            with source.open('rb') as stream:
                reader = PdfReader(stream)
                if reader.is_encrypted:
                    raise ValueError('Encrypted PDF is not supported')
                count = len(reader.pages)
            unit, start, size = 'page', 1, self.pdf_pages
        elif source.suffix.lower() == '.docx':
            count = sum(1 for _ in self._docx_blocks(source))
            unit, start, size = 'native_block', 0, self.docx_blocks
        else:
            raise ValueError(f'Unsupported source suffix: {source.suffix}')
        if not count:
            raise ValueError('Source has no pages or body blocks')
        parts = tuple(ExtractionPart(f'{unit}-{left}-{min(left + size - 1, start + count - 1)}',
                                    index, PartStatus.PENDING, left,
                                    min(left + size - 1, start + count - 1))
                      for index, left in enumerate(range(start, start + count, size)))
        return unit, parts

    def materialize(self, source: Path, part: ExtractionPart, destination: Path):
        if source.suffix.lower() == '.pdf':
            from pypdf import PdfReader, PdfWriter
            with source.open('rb') as stream:
                reader = PdfReader(stream)
                writer = PdfWriter()
                for index in range(part.source_start - 1, part.source_end):
                    writer.add_page(reader.pages[index])
                with destination.open('wb') as target:
                    writer.write(target)
        else:
            body = ET.Element(W + 'body')
            for index, block in enumerate(self._docx_blocks(source)):
                if index > part.source_end:
                    break
                if index >= part.source_start:
                    body.append(ET.fromstring(block))
            root = ET.Element(W + 'document')
            root.append(body)
            # Native extraction reads only document.xml, styles and core metadata.
            # These are internal fragments, not user-exportable DOCX documents.
            with ZipFile(source) as original, ZipFile(destination, 'w', ZIP_DEFLATED) as fragment:
                fragment.writestr('word/document.xml', ET.tostring(root, encoding='utf-8'))
                for name in ('word/styles.xml', 'docProps/core.xml'):
                    if name in original.namelist():
                        fragment.writestr(name, original.read(name))

    @staticmethod
    def _docx_blocks(source):
        with ZipFile(source) as archive, archive.open('word/document.xml') as stream:
            stack = []
            selected_depth = None
            for event, element in ET.iterparse(stream, events=('start', 'end')):
                if event == 'start':
                    stack.append(element)
                    if selected_depth is None and element.tag in {W + 'p', W + 'tbl'}:
                        if not any(parent.tag == W + 'del' for parent in stack[:-1]):
                            selected_depth = len(stack)
                else:
                    if selected_depth == len(stack):
                        yield ET.tostring(element, encoding='utf-8')
                        selected_depth = None
                    if selected_depth is None:
                        if len(stack) > 1:
                            stack[-2].remove(element)
                        element.clear()
                    stack.pop()
