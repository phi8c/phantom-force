from app.infrastructure.persistence.connection import (
    AsyncSessionLocal,
)

from app.infrastructure.persistence.repositories.document_extraction_repository_impl import (
    DocumentExtractionRepositoryImpl,
)

from app.infrastructure.persistence.unit_of_work import (
    SqlAlchemyUnitOfWork,
)

from app.shared.queue.queue_manager import (
    queue_manager,
)


class SaveExtractionDbConsumer:

    def __init__(
        self,
        save_extraction_worker,
    ):
        self.save_extraction_worker = (
            save_extraction_worker
        )

    async def start(
        self,
    ):

        queue = (
            queue_manager.get_queue(
                "save_extraction_db"
            )
        )

        while True:

            message = await (
                queue.dequeue()
            )

            async with AsyncSessionLocal() as session:

                extraction_repository = (
                    DocumentExtractionRepositoryImpl(
                        session,
                    )
                )

                uow = (
                    SqlAlchemyUnitOfWork(
                        session,
                    )
                )

                await (
                    self.save_extraction_worker.execute(
                        message=message,
                        extraction_repository=(
                            extraction_repository
                        ),
                        uow=uow,
                    )
                )