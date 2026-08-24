# app/utils/document_engine/engine.py
from app.infrastructure.providers.extraction.docling.providers.docling_provider import DoclingProvider
from app.infrastructure.providers.extraction.docling.processors.hierarchy_processor import HierarchyProcessor
from app.infrastructure.providers.extraction.docling.models.section import DocumentModel

class DocumentEngine:
    def __init__(self):
        self.provider = DoclingProvider()
        self.hierarchy_processor = HierarchyProcessor()

    def parse(self, file_path: str) -> DocumentModel:
        # 1. Pipeline lấy dữ liệu thô
        docling_doc = self.provider.parse(file_path)
        
        # 2. Xây dựng cấu trúc cây chuẩn hóa
        sections = self.hierarchy_processor.process(docling_doc)
        
        # 3. Trả về format cuối cùng không phụ thuộc Docling
        return DocumentModel(
            title=getattr(docling_doc, 'name', "Untitled Document"),
            sections=sections
        )