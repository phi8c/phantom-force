from app.application.orchestration.contracts.event_handler import (
    EventHandler,
)

from app.domain.events.document_extracted_event import (
    DocumentExtractedEvent,
)


class SaveExtractionHandler(
    EventHandler,
):

    def __init__(
        self,
        extraction_repository,
    ):
        self.extraction_repository = (
            extraction_repository
        )

    async def handle(
        self,
        event: DocumentExtractedEvent,
    ) -> None:

        await (
            self.extraction_repository.create(
                event.extraction,
            )
        )