from app.application.orchestration.contracts.event_handler import (
    EventHandler,
)

from app.domain.events.document_extracted_event import (
    DocumentExtractedEvent,
)


class DocumentExtractedHandler(
    EventHandler,
):

    async def handle(
        self,
        event: DocumentExtractedEvent,
    ) -> None:
        pass