from __future__ import annotations

import uuid
from typing import Any

from ..models import ImageModel, SectionModel, TableModel
from .metrics_processor import SectionMetricsProcessor


class UnstructuredHierarchyProcessor:
    """Maps only Unstructured semantic metadata into the RT section tree."""

    def __init__(self, metrics: SectionMetricsProcessor | None = None) -> None:
        self._metrics = metrics or SectionMetricsProcessor()
        self._warnings: list[str] = []

    @property
    def warnings(self) -> list[str]:
        return list(self._warnings)

    def process(self, elements: list[Any]) -> list[SectionModel]:
        self._warnings = []
        root_sections: list[SectionModel] = []
        stack: list[tuple[int, SectionModel]] = []
        preamble: list[str] = []

        for index, element in enumerate(elements):
            category = self._category(element)
            text = self._text(element)
            if not text and category not in {"Table", "Image"}:
                continue

            if category == "Title":
                self._append_title(root_sections, stack, element, text, index)
            elif category == "Table":
                self._append_table(stack, element)
            elif category == "Image":
                self._append_image(stack, element, text)
            elif text:
                self._append_text(stack, preamble, text)

        if preamble:
            root_sections.insert(
                0,
                SectionModel(
                    id="unstructured-preamble",
                    title="Preamble",
                    level=1,
                    content="\n".join(preamble),
                ),
            )
            self._warnings.append(
                "Document has content before the first Title; it was retained "
                "in a Preamble section."
            )

        self._metrics.process(root_sections)
        return root_sections

    def _append_title(
        self,
        roots: list[SectionModel],
        stack: list[tuple[int, SectionModel]],
        element: Any,
        text: str,
        index: int,
    ) -> None:
        level = self._heading_level(element)
        if level is None:
            self._warnings.append(
                f"Title has no reliable category_depth: {text[:120]}"
            )
            level = 1

        section = SectionModel(
            id=self._element_id(element, index),
            title=text,
            level=level,
            page_no=self._page_number(element),
        )
        while stack and stack[-1][0] >= level:
            stack.pop()
        if stack:
            stack[-1][1].children.append(section)
        else:
            roots.append(section)
        stack.append((level, section))

    def _append_table(self, stack: list[tuple[int, SectionModel]], element: Any) -> None:
        if not stack:
            self._warnings.append(
                "A table appeared before the first Title and could not be attached."
            )
            return
        stack[-1][1].tables.append(
            TableModel(
                content=self._table_content(element),
                page_no=self._page_number(element),
            )
        )

    def _append_image(
        self,
        stack: list[tuple[int, SectionModel]],
        element: Any,
        caption: str,
    ) -> None:
        if not stack:
            self._warnings.append(
                "An image appeared before the first Title and could not be attached."
            )
            return
        metadata = getattr(element, "metadata", None)
        stack[-1][1].images.append(
            ImageModel(
                image_base64=getattr(metadata, "image_base64", None),
                caption=caption or None,
                page_no=self._page_number(element),
            )
        )

    @staticmethod
    def _append_text(
        stack: list[tuple[int, SectionModel]],
        preamble: list[str],
        text: str,
    ) -> None:
        if not stack:
            preamble.append(text)
            return
        section = stack[-1][1]
        section.content = f"{section.content}\n{text}" if section.content else text

    @staticmethod
    def _category(element: Any) -> str:
        return str(getattr(element, "category", None) or type(element).__name__)

    @staticmethod
    def _text(element: Any) -> str:
        value = getattr(element, "text", "")
        return "" if value is None else str(value).strip()

    @staticmethod
    def _heading_level(element: Any) -> int | None:
        metadata = getattr(element, "metadata", None)
        depth = getattr(metadata, "category_depth", None)
        try:
            depth = int(depth)
        except (TypeError, ValueError):
            return None
        return depth + 1 if depth >= 0 else None

    @staticmethod
    def _element_id(element: Any, index: int) -> str:
        element_id = getattr(element, "id", None)
        if element_id:
            return str(element_id)
        return f"unstructured-{index}-{uuid.uuid4().hex[:8]}"

    @staticmethod
    def _page_number(element: Any) -> int | None:
        metadata = getattr(element, "metadata", None)
        value = getattr(metadata, "page_number", None)
        try:
            return int(value) if value is not None else None
        except (TypeError, ValueError):
            return None

    def _table_content(self, element: Any) -> str:
        metadata = getattr(element, "metadata", None)
        html = getattr(metadata, "text_as_html", None)
        return str(html) if html else self._text(element)
