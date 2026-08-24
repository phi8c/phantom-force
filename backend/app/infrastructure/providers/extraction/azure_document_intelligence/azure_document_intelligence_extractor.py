from uuid import uuid4
import json
from pathlib import Path

from azure.ai.documentintelligence.aio import (
    DocumentIntelligenceClient,
)

from azure.core.credentials import (
    AzureKeyCredential,
)

from app.domain.ports.extraction.document_extractor import (
    DocumentExtractor,
)

from app.shared.config.settings import (
    settings,
)


class AzureDocumentIntelligenceExtractor(
    DocumentExtractor,
):

    def __init__(
        self,
    ):
        self.client = (
            DocumentIntelligenceClient(
                endpoint=(
                    settings
                    .AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT
                ),
                credential=(
                    AzureKeyCredential(
                        settings
                        .AZURE_DOCUMENT_INTELLIGENCE_KEY
                    )
                ),
            )
        )

    async def extract(
        self,
        file_path: str,
    ) -> dict:

        debug_dir = Path(
            "temp/debug"
        )

        debug_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        with open(
            file_path,
            "rb",
        ) as file:

            poller = await (
                self.client.begin_analyze_document(
                    model_id="prebuilt-layout",
                    body=file,
                )
            )

            result = await (
                poller.result()
            )

        # ==================================
        # BASIC INFO
        # ==================================

        print(
            "\n========== DI RESULT =========="
        )

        print(
            "PAGES =",
            len(
                result.pages or []
            ),
        )

        print(
            "PARAGRAPHS =",
            len(
                result.paragraphs or []
            ),
        )

        print(
            "TABLES =",
            len(
                result.tables or []
            ),
        )

        print(
            "FIGURES =",
            len(
                result.figures or []
            ),
        )

        print(
            "SECTIONS =",
            len(
                getattr(
                    result,
                    "sections",
                    [],
                )
                or []
            ),
        )

        # ==================================
        # DUMP PARAGRAPHS
        # ==================================

        paragraphs_dump = []

        if result.paragraphs:

            for idx, paragraph in enumerate(
                result.paragraphs
            ):

                item = {
                    "index": idx,
                    "content": (
                        paragraph.content
                    ),
                    "role": getattr(
                        paragraph,
                        "role",
                        None,
                    ),
                }

                paragraphs_dump.append(
                    item
                )

                print(
                    f"\nPARAGRAPH {idx}"
                )

                print(
                    "ROLE =",
                    item["role"],
                )

                print(
                    "CONTENT =",
                    item["content"],
                )

        with open(
            debug_dir
            / "paragraphs.json",
            "w",
            encoding="utf-8",
        ) as f:

            json.dump(
                paragraphs_dump,
                f,
                ensure_ascii=False,
                indent=2,
            )

        # ==================================
        # DUMP TABLES
        # ==================================

        tables_dump = []

        if result.tables:

            for idx, table in enumerate(
                result.tables
            ):

                table_info = {
                    "index": idx,
                    "row_count": (
                        table.row_count
                    ),
                    "column_count": (
                        table.column_count
                    ),
                    "cells": [],
                }

                for cell in table.cells:

                    table_info[
                        "cells"
                    ].append(
                        {
                            "row": (
                                cell.row_index
                            ),
                            "column": (
                                cell.column_index
                            ),
                            "content": (
                                cell.content
                            ),
                        }
                    )

                tables_dump.append(
                    table_info
                )

        with open(
            debug_dir
            / "tables.json",
            "w",
            encoding="utf-8",
        ) as f:

            json.dump(
                tables_dump,
                f,
                ensure_ascii=False,
                indent=2,
            )

        # ==================================
        # DUMP FIGURES
        # ==================================

        figures_dump = []

        if result.figures:

            for idx, figure in enumerate(
                result.figures
            ):

                figures_dump.append(
                    str(
                        figure
                    )
                )

        with open(
            debug_dir
            / "figures.json",
            "w",
            encoding="utf-8",
        ) as f:

            json.dump(
                figures_dump,
                f,
                ensure_ascii=False,
                indent=2,
            )

        # ==================================
        # RAW RESULT
        # ==================================

        with open(
            debug_dir
            / "raw_result.txt",
            "w",
            encoding="utf-8",
        ) as f:

            f.write(
                str(result)
            )

        # ==================================
        # CURRENT OUTPUT
        # ==================================

        elements = []

        if result.paragraphs:

            for paragraph in result.paragraphs:

                content = (
                    paragraph.content
                    or ""
                ).strip()

                if not content:
                    continue

                elements.append(
                    {
                        "id": str(
                            uuid4()
                        ),
                        "type": "paragraph",
                        "role": getattr(
                            paragraph,
                            "role",
                            None,
                        ),
                        "hierarchy": [],
                        "text": content,
                    }
                )

        if result.tables:

            for table in result.tables:

                rows = [
                    [
                        ""
                        for _ in range(
                            table.column_count
                        )
                    ]
                    for _ in range(
                        table.row_count
                    )
                ]

                for cell in table.cells:

                    rows[
                        cell.row_index
                    ][
                        cell.column_index
                    ] = (
                        cell.content
                    )

                elements.append(
                    {
                        "id": str(
                            uuid4()
                        ),
                        "type": "table",
                        "hierarchy": [],
                        "row_count": (
                            table.row_count
                        ),
                        "column_count": (
                            table.column_count
                        ),
                        "rows": rows,
                    }
                )

        return {
            "page_count": len(
                result.pages or []
            ),
            "elements": elements,
        }