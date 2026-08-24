import json
from uuid import UUID

from azure.servicebus.aio import (
    ServiceBusClient,
)

from app.infrastructure.persistence.connection import (
    AsyncSessionLocal,
)

from app.infrastructure.persistence.repositories.document_repository_impl import (
    DocumentRepositoryImpl,
)

from app.infrastructure.persistence.unit_of_work import (
    SqlAlchemyUnitOfWork,
)


class DownloadConsumer:

    def __init__(
        self,
        connection_string,
        queue_name,
        download_worker,
    ):
        self.connection_string = (
            connection_string
        )

        self.queue_name = (
            queue_name
        )

        self.download_worker = (
            download_worker
        )

    async def start(
        self,
    ):

        client = (
            ServiceBusClient.from_connection_string(
                self.connection_string,
            )
        )

        async with client:

            receiver = (
                client.get_queue_receiver(
                    queue_name=(
                        self.queue_name
                    )
                )
            )

            async with receiver:

                async for message in receiver:

                    payload = json.loads(
                        str(message)
                    )

                    print(payload)

                    document_id = UUID(
                        payload[
                            "document_id"
                        ]
                    )

                    async with AsyncSessionLocal() as session:

                        document_repository = (
                            DocumentRepositoryImpl(
                                session,
                            )
                        )

                        uow = (
                            SqlAlchemyUnitOfWork(
                                session,
                            )
                        )

                        document = await (
                            document_repository
                            .get_by_id(
                                document_id,
                            )
                        )

                        if document:

                            await (
                                self.download_worker.execute(
                                    document=document,
                                    document_repository=(
                                        document_repository
                                    ),
                                    uow=uow,
                                )
                            )

                    await (
                        receiver.complete_message(
                            message,
                        )
                    )