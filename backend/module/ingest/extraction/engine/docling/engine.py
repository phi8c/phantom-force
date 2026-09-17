from module.ingest.extraction.engine.docling.models.section import (
    DocumentModel,
)
from module.ingest.extraction.engine.docling.processors.docx_structure_processor import (
    DocxStructureProcessor,
)
from module.ingest.extraction.engine.docling.processors.hierarchy_processor import (
    HierarchyProcessor,
)
from module.ingest.extraction.engine.docling.providers.docling_provider import (
    DoclingProvider,
)


class DocumentEngine:

    def __init__(self):
        self.provider = DoclingProvider()
        self.hierarchy_processor = HierarchyProcessor()
        self.docx_structure_processor = (
            DocxStructureProcessor()
        )

    def parse(
        self,
        file_path: str,
    ) -> DocumentModel:

        docling_doc = self.provider.parse(
            file_path,
        )

        sections = self.hierarchy_processor.process(
            docling_doc,
        )

        if (
            not sections
            and str(file_path).lower().endswith(".docx")
        ):
            print(
                "docx_structure fallback_start "
                f"file_path={file_path}",
                flush=True,
            )
            sections = (
                self.docx_structure_processor
                .process(
                    file_path,
                )
            )
            print(
                "docx_structure fallback_done "
                f"file_path={file_path} "
                f"sections={len(sections)}",
                flush=True,
            )

        return DocumentModel(
            title=getattr(
                docling_doc,
                "name",
                "Untitled Document",
            ),
            sections=sections,
        )
