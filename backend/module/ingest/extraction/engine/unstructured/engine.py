from __future__ import annotations

from pathlib import Path
from typing import Any

from .contracts import ElementSerializer, PartitionProvider, SectionProcessor
from .models import DocumentModel
from .processors import UnstructuredHierarchyProcessor
from .providers import UnstructuredProvider
from .serializers import UnstructuredElementSerializer


SUPPORTED_SUFFIXES = {".docx", ".pdf"}


class UnstructuredEngine:
    """Coordinates Unstructured extraction without depending on Docling."""

    def __init__(
        self,
        pdf_strategy: str = "hi_res",
        *,
        provider: PartitionProvider | None = None,
        section_processor: SectionProcessor | None = None,
        element_serializer: ElementSerializer | None = None,
    ) -> None:
        self._provider = provider or UnstructuredProvider(pdf_strategy=pdf_strategy)
        self._section_processor = section_processor or UnstructuredHierarchyProcessor()
        self._element_serializer = element_serializer or UnstructuredElementSerializer()
        self.warnings: list[str] = []
        self.raw_elements: list[dict[str, Any]] = []

    def parse(self, file_path: str | Path) -> DocumentModel:
        path = Path(file_path)
        self._validate_path(path)

        elements = self._provider.partition(path)
        self.raw_elements = [
            self._element_serializer.serialize(element) for element in elements
        ]
        sections = self._section_processor.process(elements)
        self.warnings = self._section_processor.warnings

        return DocumentModel(title=path.stem, sections=sections)

    @staticmethod
    def _validate_path(path: Path) -> None:
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")
        if not path.is_file():
            raise ValueError(f"Path is not a file: {path}")
        if path.suffix.lower() not in SUPPORTED_SUFFIXES:
            supported = ", ".join(sorted(SUPPORTED_SUFFIXES))
            raise ValueError(
                f"Unstructured engine supports only {supported}. Got: {path.suffix}"
            )


# Backward-compatible name used by the existing prototype runner.
UnstructuredPrototypeEngine = UnstructuredEngine
