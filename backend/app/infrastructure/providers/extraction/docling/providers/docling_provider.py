# app/utils/document_engine/providers/docling_provider.py
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.datamodel.base_models import InputFormat

class DoclingProvider:
    def __init__(self):
        pipeline_options = PdfPipelineOptions()
        # BẮT BUỘC để giải quyết Lỗi 3 (PICTURE COUNT = 0)
        pipeline_options.generate_picture_images = True 
        pipeline_options.do_table_structure = True
        
        self.converter = DocumentConverter(
            allowed_formats=[InputFormat.PDF, InputFormat.DOCX],
            format_options={
                InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
            }
        )

    def parse(self, file_path: str):
        return self.converter.convert(file_path).document