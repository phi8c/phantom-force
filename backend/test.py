import asyncio
import json
import zipfile
from collections import Counter
from pathlib import Path
from uuid import uuid4

from module.ingest.chunking.engine.models.document_extraction import (
    DocumentExtraction,
)
from module.ingest.chunking.engine.strategies.level_chunk_strategy import (
    LevelChunkStrategy,
)
from module.ingest.extraction.engine.docling.engine import (
    DocumentEngine,
)
from module.ingest.extraction.infrastructure.engine.docling_extraction_engine import (
    DoclingExtractionEngine,
)


# TODO: dien path document can test vao day.
DOCUMENT_PATH = r"D:\pico_azure_rag\temp\Bao_Cao_Nhan_Dinh_Thi_Truong_Bat_Dong_San_2026_2029.docx"

# Hard-code SECTION strategy nhu pipeline hien tai.
CHUNKING_STRATEGY_CODE = "SECTION"
TARGET_LEVEL = 2


async def main() -> None:
    path = Path(DOCUMENT_PATH)

    print("\n===== TEST INPUT START =====", flush=True)
    print(f"path={path}", flush=True)
    print(f"exists={path.exists()}", flush=True)
    print(f"suffix={path.suffix}", flush=True)
    if path.exists():
        print(f"size_bytes={path.stat().st_size}", flush=True)
    print("===== TEST INPUT END =====\n", flush=True)

    if not path.exists():
        raise FileNotFoundError(path)

    _print_file_preview(path)
    _print_zip_entries(path)

    print("\n===== DOCLING RAW ITEMS START =====", flush=True)
    document_engine = DocumentEngine()
    docling_doc = document_engine.provider.parse(path)
    _print_docling_items(docling_doc)
    print("===== DOCLING RAW ITEMS END =====\n", flush=True)

    print("\n===== HIERARCHY PROCESSOR OUTPUT START =====", flush=True)
    sections = document_engine.hierarchy_processor.process(
        docling_doc,
    )
    print(f"sections_count={_count_sections(sections)}", flush=True)
    print(f"section_levels={_collect_section_levels(sections)}", flush=True)
    for section in sections:
        print(
            section.model_dump(),
            flush=True,
        )
    print("===== HIERARCHY PROCESSOR OUTPUT END =====\n", flush=True)

    print("\n===== EXTRACTION ENGINE OUTPUT START =====", flush=True)
    extraction_engine = DoclingExtractionEngine()
    extraction_result = await extraction_engine.extract(path)
    print(f"content_type={extraction_result.content_type}", flush=True)
    print(
        json.dumps(
            extraction_result.content,
            ensure_ascii=False,
            indent=2,
            default=str,
        ),
        flush=True,
    )
    print("===== EXTRACTION ENGINE OUTPUT END =====\n", flush=True)

    print("\n===== TEST CHUNKING START =====", flush=True)
    print(f"strategy_code={CHUNKING_STRATEGY_CODE}", flush=True)
    print(f"target_level={TARGET_LEVEL}", flush=True)
    extraction = DocumentExtraction(
        id=None,
        document_id=uuid4(),
        structured_content=extraction_result.content,
        page_count=(
            extraction_result.content.get("page_count")
            if isinstance(extraction_result.content, dict)
            else None
        ),
        created_at=None,
    )

    chunks = list(
        LevelChunkStrategy(
            level=TARGET_LEVEL,
        ).chunk(
            extraction,
        )
    )

    print(f"chunks_count={len(chunks)}", flush=True)
    for chunk in chunks:
        print(chunk, flush=True)
    print("===== TEST CHUNKING END =====\n", flush=True)


def _print_file_preview(path: Path) -> None:
    data = path.read_bytes()[:512]

    print("\n===== FILE PREVIEW START =====", flush=True)
    print(f"preview_hex={data.hex()}", flush=True)
    print(
        "preview_text="
        f"{data.decode('utf-8', errors='replace')}",
        flush=True,
    )
    print("===== FILE PREVIEW END =====\n", flush=True)


def _print_zip_entries(path: Path) -> None:
    print("\n===== ZIP ENTRIES START =====", flush=True)

    if not zipfile.is_zipfile(path):
        print("is_zipfile=False", flush=True)
        print("===== ZIP ENTRIES END =====\n", flush=True)
        return

    print("is_zipfile=True", flush=True)

    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        print(f"entries_count={len(names)}", flush=True)
        print(
            f"has_word_document_xml={'word/document.xml' in names}",
            flush=True,
        )
        print(
            f"has_content_types={'[Content_Types].xml' in names}",
            flush=True,
        )

        for name in names:
            info = archive.getinfo(name)
            print(
                f"{name} size={info.file_size} "
                f"compressed={info.compress_size}",
                flush=True,
            )

        if "word/document.xml" in names:
            xml = archive.read("word/document.xml")[:2000]
            print("\n----- word/document.xml preview -----", flush=True)
            print(
                xml.decode("utf-8", errors="replace"),
                flush=True,
            )

    print("===== ZIP ENTRIES END =====\n", flush=True)


def _print_docling_items(docling_doc) -> None:
    labels = Counter()
    total = 0

    for item, _ in docling_doc.iterate_items():
        total += 1
        label = getattr(item, "label", None)
        labels[str(label)] += 1

        text = getattr(item, "text", None)
        level = getattr(item, "level", None)
        self_ref = getattr(item, "self_ref", None)
        prov = getattr(item, "prov", None)
        page_no = (
            prov[0].page_no
            if prov
            else None
        )

        print(
            "docling_item "
            f"index={total} "
            f"label={label} "
            f"level={level} "
            f"page_no={page_no} "
            f"self_ref={self_ref} "
            f"text={text!r}",
            flush=True,
        )

    print(f"docling_items_total={total}", flush=True)
    print(f"docling_label_distribution={dict(labels)}", flush=True)


def _count_sections(sections: list) -> int:
    count = 0
    stack = list(reversed(sections))

    while stack:
        section = stack.pop()
        count += 1
        stack.extend(reversed(section.children))

    return count


def _collect_section_levels(sections: list) -> dict:
    levels = Counter()
    stack = list(reversed(sections))

    while stack:
        section = stack.pop()
        levels[section.level] += 1
        stack.extend(reversed(section.children))

    return dict(sorted(levels.items()))


if __name__ == "__main__":
    asyncio.run(main())
