from collections import deque

from ..models.document import (
    Document
)

from ..models.section import (
    Section
)

from ..mappers.table_mapper import (
    TableMapper
)


class DocumentBuilder:

    def build(
        self,
        doc,
    ) -> Document:

        document = Document()

        sections = []

        current_section = None

        section_id = 0

        for item in doc.texts:

            item_type = (
                type(item).__name__
            )

            if (
                item_type
                == "SectionHeaderItem"
            ):

                section_id += 1

                level = getattr(
                    item,
                    "level",
                    1,
                )

                current_section = (
                    Section(
                        id=str(section_id),
                        title=item.text,
                        level=level,
                    )
                )

                sections.append(
                    current_section
                )

                continue

            if (
                current_section
                is None
            ):

                section_id += 1

                current_section = (
                    Section(
                        id=str(section_id),
                        title="ROOT",
                        level=0,
                    )
                )

                sections.append(
                    current_section
                )

            text = getattr(
                item,
                "text",
                "",
            )

            if text:

                current_section.content += (
                    text + "\n"
                )

        document.sections = (
            sections
        )

        self._attach_tables(
            document,
            doc,
        )

        return document

    def _attach_tables(
        self,
        document,
        doc,
    ):

        if (
            not document.sections
        ):
            return

        section_queue = deque(
            document.sections
        )

        idx = 0

        for table in doc.tables:

            section = (
                document.sections[
                    min(
                        idx,
                        len(
                            document.sections
                        )
                        - 1,
                    )
                ]
            )

            mapped = (
                TableMapper.map_table(
                    table,
                    idx + 1,
                )
            )

            section.tables.append(
                mapped
            )

            idx += 1