from collections.abc import Iterator


class ParagraphSplitter:

    def split(
        self,
        content: str,
    ) -> Iterator[str]:

        if not content:
            return

        for paragraph in content.split(
            "\n",
        ):

            normalized = (
                paragraph.strip()
            )

            if not normalized:
                continue

            yield normalized