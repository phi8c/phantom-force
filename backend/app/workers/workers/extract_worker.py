from app.application.ingestion.messages.save_extraction_message import (
    SaveExtractionMessage,
)


class ExtractWorker:

    def __init__(
        self,
        extractor,
        original_file_storage,
        temp_storage,
        save_extraction_dispatcher,
    ):
        self.extractor = (
            extractor
        )

        self.original_file_storage = (
            original_file_storage
        )

        self.temp_storage = (
            temp_storage
        )

        self.save_extraction_dispatcher = (
            save_extraction_dispatcher
        )

    async def execute(
        self,
        document,
    ):

        content = await (
            self.original_file_storage.download(
                document.original_file_path,
            )
        )

        temp_path = await (
            self.temp_storage.save(
                file_name=(
                    f"{document.id}"
                    f".{document.file_extension}"
                ),
                content=content,
            )
        )

        extraction = await (
            self.extractor.extract(
                temp_path,
            )
        )

        await (
            self.save_extraction_dispatcher.dispatch(
                SaveExtractionMessage(
                    document_id=document.id,
                    extraction=extraction,
                )
            )
        )