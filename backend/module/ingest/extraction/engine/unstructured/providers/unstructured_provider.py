from __future__ import annotations

from pathlib import Path
from typing import Any


class UnstructuredProvider:
    """Adapter around the external Unstructured partition APIs."""

    def __init__(self, pdf_strategy: str = "hi_res") -> None:
        self._pdf_strategy = pdf_strategy

    def partition(self, file_path: Path) -> list[Any]:
        if file_path.suffix.lower() == ".docx":
            from unstructured.partition.docx import partition_docx

            return list(partition_docx(filename=str(file_path), include_page_breaks=True))

        if file_path.suffix.lower() == ".pdf":
            from unstructured.partition.pdf import partition_pdf

            return list(
                partition_pdf(
                    filename=str(file_path),
                    strategy=self._pdf_strategy,
                    infer_table_structure=True,
                )
            )

        raise ValueError(f"Unsupported suffix: {file_path.suffix.lower()}")
