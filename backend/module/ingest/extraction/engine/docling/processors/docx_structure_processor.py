import re
import statistics
import zipfile
from dataclasses import dataclass
from pathlib import Path
from xml.etree import ElementTree

from module.ingest.extraction.engine.docling.models.section import (
    SectionModel,
)
from module.ingest.extraction.engine.docling.processors.text_processor import (
    clean_text,
)


WORD_NS = {
    "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
}


@dataclass
class ParagraphInfo:
    index: int
    text: str
    style_id: str | None
    style_name: str | None
    outline_level: int | None
    numbering_level: int | None
    alignment: str | None
    is_bold: bool
    font_size_half_points: int | None


class DocxStructureProcessor:
    """
    DOCX fallback for files where Docling returns only plain text items.

    The primary signal is Word structure: paragraph style, outline level,
    numbering level, and direct formatting. Text patterns are only used as
    a narrow fallback when the DOCX has no semantic heading styles.
    """

    def process(
        self,
        file_path: Path,
    ) -> list[SectionModel]:

        if not zipfile.is_zipfile(
            file_path,
        ):
            return []

        with zipfile.ZipFile(
            file_path,
        ) as archive:
            if "word/document.xml" not in archive.namelist():
                return []

            styles = self._load_styles(
                archive,
            )
            document_root = ElementTree.fromstring(
                archive.read(
                    "word/document.xml",
                )
            )

        paragraphs = self._read_paragraphs(
            document_root,
            styles,
        )

        return self._build_sections(
            paragraphs,
        )

    def _load_styles(
        self,
        archive: zipfile.ZipFile,
    ) -> dict:

        if "word/styles.xml" not in archive.namelist():
            return {}

        root = ElementTree.fromstring(
            archive.read(
                "word/styles.xml",
            )
        )
        styles = {}

        for style in root.findall(
            "w:style",
            WORD_NS,
        ):
            style_id = self._attr(
                style,
                "styleId",
            )

            if not style_id:
                continue

            name_node = style.find(
                "w:name",
                WORD_NS,
            )
            outline_node = style.find(
                "w:pPr/w:outlineLvl",
                WORD_NS,
            )
            bold_node = style.find(
                "w:rPr/w:b",
                WORD_NS,
            )
            size_node = style.find(
                "w:rPr/w:sz",
                WORD_NS,
            )

            styles[style_id] = {
                "name": (
                    self._attr(
                        name_node,
                        "val",
                    )
                    if name_node is not None
                    else None
                ),
                "outline_level": (
                    self._int_attr(
                        outline_node,
                        "val",
                    )
                    if outline_node is not None
                    else None
                ),
                "is_bold": bold_node is not None,
                "font_size_half_points": (
                    self._int_attr(
                        size_node,
                        "val",
                    )
                    if size_node is not None
                    else None
                ),
            }

        return styles

    def _read_paragraphs(
        self,
        document_root: ElementTree.Element,
        styles: dict,
    ) -> list[ParagraphInfo]:

        paragraphs = []
        body = document_root.find(
            "w:body",
            WORD_NS,
        )

        if body is None:
            return paragraphs

        for index, paragraph in enumerate(
            body.findall(
                "w:p",
                WORD_NS,
            )
        ):
            text = clean_text(
                "".join(
                    node.text or ""
                    for node in paragraph.findall(
                        ".//w:t",
                        WORD_NS,
                    )
                )
            )

            if not text:
                continue

            p_pr = paragraph.find(
                "w:pPr",
                WORD_NS,
            )
            style_id = self._paragraph_style_id(
                p_pr,
            )
            style = styles.get(
                style_id,
                {},
            )

            paragraphs.append(
                ParagraphInfo(
                    index=index,
                    text=text,
                    style_id=style_id,
                    style_name=style.get(
                        "name",
                    ),
                    outline_level=style.get(
                        "outline_level",
                    ),
                    numbering_level=self._numbering_level(
                        p_pr,
                    ),
                    alignment=self._alignment(
                        p_pr,
                    ),
                    is_bold=(
                        style.get(
                            "is_bold",
                            False,
                        )
                        or self._has_direct_bold(
                            paragraph,
                        )
                    ),
                    font_size_half_points=(
                        self._direct_font_size(
                            paragraph,
                        )
                        or style.get(
                            "font_size_half_points",
                        )
                    ),
                )
            )

        return paragraphs

    def _build_sections(
        self,
        paragraphs: list[ParagraphInfo],
    ) -> list[SectionModel]:

        if not paragraphs:
            return []

        body_size = self._body_font_size(
            paragraphs,
        )
        heading_levels = [
            self._heading_level(
                paragraph,
                body_size,
            )
            for paragraph in paragraphs
        ]

        if not any(
            level is not None
            for level in heading_levels
        ):
            return self._single_section(
                paragraphs,
            )

        ghost_root = SectionModel(
            id="docx-root",
            title="Root",
            level=0,
            page_no=1,
        )
        stack = [
            (
                0,
                ghost_root,
            )
        ]

        for paragraph, level in zip(
            paragraphs,
            heading_levels,
        ):
            if level is not None:
                section = SectionModel(
                    id=f"docx-p-{paragraph.index}",
                    title=paragraph.text,
                    level=level,
                    page_no=None,
                )

                while stack and stack[-1][0] >= level:
                    stack.pop()

                stack[-1][1].children.append(
                    section,
                )
                stack.append(
                    (
                        level,
                        section,
                    )
                )
                continue

            if stack[-1][1].id == "docx-root":
                section = SectionModel(
                    id=f"docx-preamble-{paragraph.index}",
                    title="Preamble",
                    level=1,
                    page_no=None,
                )
                stack[-1][1].children.append(
                    section,
                )
                stack.append(
                    (
                        1,
                        section,
                    )
                )

            current = stack[-1][1]
            current.content = (
                f"{current.content}\n{paragraph.text}"
                if current.content
                else paragraph.text
            )

        for section in ghost_root.children:
            self._calculate_metrics(
                section,
            )

        return ghost_root.children

    def _heading_level(
        self,
        paragraph: ParagraphInfo,
        body_size: int | None,
    ) -> int | None:

        style_level = self._style_heading_level(
            paragraph,
        )

        if style_level is not None:
            return style_level

        if paragraph.outline_level is not None:
            return paragraph.outline_level + 1

        numbered_level = self._numbered_heading_level(
            paragraph.text,
        )

        if numbered_level is not None and self._looks_like_heading(
            paragraph,
            body_size,
        ):
            return numbered_level

        if self._format_heading_score(
            paragraph,
            body_size,
        ) >= 3:
            return 1

        return None

    def _style_heading_level(
        self,
        paragraph: ParagraphInfo,
    ) -> int | None:

        style_text = " ".join(
            value
            for value in [
                paragraph.style_id,
                paragraph.style_name,
            ]
            if value
        ).lower()

        match = re.search(
            r"\bheading\s*([1-9])",
            style_text,
        )

        if match:
            return int(
                match.group(
                    1,
                )
            )

        match = re.search(
            r"\btitle\s*([1-9])",
            style_text,
        )

        if match:
            return int(
                match.group(
                    1,
                )
            )

        return None

    def _numbered_heading_level(
        self,
        text: str,
    ) -> int | None:

        match = re.match(
            r"^\s*(\d+(?:\.\d+){0,5})[\.\)]?\s+\S+",
            text,
        )

        if not match:
            return None

        return min(
            match.group(
                1,
            ).count(".") + 1,
            6,
        )

    def _looks_like_heading(
        self,
        paragraph: ParagraphInfo,
        body_size: int | None,
    ) -> bool:

        words = paragraph.text.split()

        if len(words) > 24:
            return False

        return (
            paragraph.is_bold
            or paragraph.numbering_level is not None
            or self._font_size_delta(
                paragraph,
                body_size,
            )
            >= 1
        )

    def _format_heading_score(
        self,
        paragraph: ParagraphInfo,
        body_size: int | None,
    ) -> int:

        words = paragraph.text.split()

        if len(words) > 18:
            return 0

        score = 0

        if paragraph.is_bold:
            score += 1

        if paragraph.alignment in {
            "center",
            "both",
        }:
            score += 1

        if self._font_size_delta(
            paragraph,
            body_size,
        ) >= 4:
            score += 2
        elif self._font_size_delta(
            paragraph,
            body_size,
        ) >= 2:
            score += 1

        if self._uppercase_ratio(
            paragraph.text,
        ) >= 0.7:
            score += 1

        return score

    def _single_section(
        self,
        paragraphs: list[ParagraphInfo],
    ) -> list[SectionModel]:

        section = SectionModel(
            id="docx-document",
            title=paragraphs[0].text[:120],
            level=1,
            content="\n".join(
                paragraph.text
                for paragraph in paragraphs
            ),
        )
        self._calculate_metrics(
            section,
        )
        return [
            section,
        ]

    def _calculate_metrics(
        self,
        section: SectionModel,
    ) -> tuple[str, int]:

        aggregated_content = section.content
        token_count = self._estimate_tokens(
            section.content,
        )
        aggregated_token_count = token_count

        for child in section.children:
            child_content, child_token_count = (
                self._calculate_metrics(
                    child,
                )
            )

            if child_content:
                aggregated_content = (
                    f"{aggregated_content}\n\n{child_content}"
                    if aggregated_content
                    else child_content
                )

            aggregated_token_count += child_token_count

        section.token_count = token_count
        section.aggregated_content = aggregated_content
        section.aggregated_token_count = aggregated_token_count

        return (
            aggregated_content,
            aggregated_token_count,
        )

    def _body_font_size(
        self,
        paragraphs: list[ParagraphInfo],
    ) -> int | None:

        sizes = [
            paragraph.font_size_half_points
            for paragraph in paragraphs
            if paragraph.font_size_half_points is not None
        ]

        if not sizes:
            return None

        return int(
            statistics.median(
                sizes,
            )
        )

    def _font_size_delta(
        self,
        paragraph: ParagraphInfo,
        body_size: int | None,
    ) -> int:

        if (
            body_size is None
            or paragraph.font_size_half_points is None
        ):
            return 0

        return paragraph.font_size_half_points - body_size

    def _uppercase_ratio(
        self,
        text: str,
    ) -> float:

        letters = [
            char
            for char in text
            if char.isalpha()
        ]

        if not letters:
            return 0

        uppercase = [
            char
            for char in letters
            if char.upper() == char
        ]

        return len(
            uppercase,
        ) / len(
            letters,
        )

    def _paragraph_style_id(
        self,
        p_pr: ElementTree.Element | None,
    ) -> str | None:

        if p_pr is None:
            return None

        node = p_pr.find(
            "w:pStyle",
            WORD_NS,
        )

        return self._attr(
            node,
            "val",
        )

    def _numbering_level(
        self,
        p_pr: ElementTree.Element | None,
    ) -> int | None:

        if p_pr is None:
            return None

        node = p_pr.find(
            "w:numPr/w:ilvl",
            WORD_NS,
        )

        return self._int_attr(
            node,
            "val",
        )

    def _alignment(
        self,
        p_pr: ElementTree.Element | None,
    ) -> str | None:

        if p_pr is None:
            return None

        node = p_pr.find(
            "w:jc",
            WORD_NS,
        )

        return self._attr(
            node,
            "val",
        )

    def _has_direct_bold(
        self,
        paragraph: ElementTree.Element,
    ) -> bool:

        return paragraph.find(
            ".//w:rPr/w:b",
            WORD_NS,
        ) is not None

    def _direct_font_size(
        self,
        paragraph: ElementTree.Element,
    ) -> int | None:

        sizes = [
            self._int_attr(
                node,
                "val",
            )
            for node in paragraph.findall(
                ".//w:rPr/w:sz",
                WORD_NS,
            )
        ]
        sizes = [
            size
            for size in sizes
            if size is not None
        ]

        if not sizes:
            return None

        return max(
            sizes,
        )

    def _attr(
        self,
        node: ElementTree.Element | None,
        name: str,
    ) -> str | None:

        if node is None:
            return None

        return node.attrib.get(
            f"{{{WORD_NS['w']}}}{name}",
        )

    def _int_attr(
        self,
        node: ElementTree.Element | None,
        name: str,
    ) -> int | None:

        value = self._attr(
            node,
            name,
        )

        if value is None:
            return None

        try:
            return int(
                value,
            )
        except ValueError:
            return None

    def _estimate_tokens(
        self,
        text: str,
    ) -> int:

        if not text:
            return 0

        return len(
            text.split(),
        )
