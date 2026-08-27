from ..models.table import TableBlock


class TableMapper:

    @staticmethod
    def map_table(table, table_id: int):

        rows = []

        try:
            df = table.export_to_dataframe()

            if df is not None:
                rows = df.to_dict(
                    orient="records"
                )

        except Exception as ex:
            print(
                f"TABLE ERROR: {ex}"
            )

        caption = None

        try:

            if callable(
                getattr(
                    table,
                    "caption_text",
                    None,
                )
            ):
                caption = (
                    table.caption_text()
                )
            else:
                caption = (
                    getattr(
                        table,
                        "caption_text",
                        None,
                    )
                )

        except Exception:
            pass

        return TableBlock(
            id=f"table_{table_id}",
            caption=caption,
            rows=rows,
        )