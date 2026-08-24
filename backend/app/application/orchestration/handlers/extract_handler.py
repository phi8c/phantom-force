from app.application.orchestration.contracts.event_bus import (
    EventBus,
)

from app.application.orchestration.contracts.event_handler import (
    EventHandler,
)

from app.domain.entities.document_extraction import (
    DocumentExtraction,
)

from app.domain.events.document_downloaded_event import (
    DocumentDownloadedEvent,
)

from app.domain.events.document_extracted_event import (
    DocumentExtractedEvent,
)


class ExtractHandler(
    EventHandler,
):

    def __init__(
        self,
        document_extractor,
        event_bus: EventBus,
    ):
        self.document_extractor = (
            document_extractor
        )

        self.event_bus = (
            event_bus
        )

    async def handle(
        self,
        event: DocumentDownloadedEvent,
    ) -> None:

        structured_document = (
            await self.document_extractor.extract(
                event.temp_file_path,
            )
        )

        structured_content = (
            structured_document.model_dump()
        )

        extraction = (
            DocumentExtraction(
                id=None,
                document_id=(
                    event.document_id
                ),
                structured_content=(
                    structured_content
                ),
                page_count=None,
                created_at=None,
            )
        )

        await self.event_bus.publish(
            DocumentExtractedEvent.create(
                document_id=(
                    event.document_id
                ),
                extraction=(
                    extraction
                ),
            )
        )