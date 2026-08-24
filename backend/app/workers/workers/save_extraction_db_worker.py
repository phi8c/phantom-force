from datetime import (
    datetime,
    timezone,
)

from app.application.ingestion.messages.chunk_message import (
    ChunkMessage,
)

from app.domain.entities.document_extraction import (
    DocumentExtraction,
)

from app.domain.repositories.document_extraction_repository import (
    DocumentExtractionRepository,
)

from app.infrastructure.persistence.unit_of_work import (
    SqlAlchemyUnitOfWork,
)
from app.shared.queue.queue_manager import (
    queue_manager,
)

class SaveExtractionDbWorker:

    def __init__(
        self,
        chunk_dispatcher,
    ):
        self.chunk_dispatcher = (
            chunk_dispatcher
        )

    async def execute(
        self,
        message,
        extraction_repository: DocumentExtractionRepository,
        uow: SqlAlchemyUnitOfWork,
    ):

        extraction = DocumentExtraction(
            id=None,
            document_id=message.document_id,
            structured_content=message.extraction.model_dump(),
            page_count=None,
            created_at=datetime.now(
                timezone.utc,
            ),
        )

        extraction = await (
            extraction_repository.create(
                extraction,
            )
        )

        await (
            uow.commit()
        )

        chunk_message = ChunkMessage(
            document_id=message.document_id,
            extraction_id=extraction.id,
        )

        # Local Queue (debug)
        await (
            queue_manager.get_queue(
                "chunk",
            ).enqueue(
                chunk_message,
            )
        )

        # Azure Service Bus
        await (
            self.chunk_dispatcher.dispatch(
                chunk_message,
            )
        )