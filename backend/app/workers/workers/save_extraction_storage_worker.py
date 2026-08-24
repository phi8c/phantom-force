from app.application.ingestion.messages.save_extraction_message import (
    SaveExtractionMessage,
)



class SaveExtractionStorageWorker:

    def __init__(
        self,
        extraction_storage,
    ):
        self.extraction_storage = (
            extraction_storage
        )

    async def execute(
        self,
        message: SaveExtractionMessage,
    ):

        await (
            self.extraction_storage.upload_extraction(
                message,
            )
        )