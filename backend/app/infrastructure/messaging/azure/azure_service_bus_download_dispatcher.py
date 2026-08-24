import json
from uuid import UUID

from azure.servicebus import (
    ServiceBusMessage,
)

from azure.servicebus.aio import (
    ServiceBusClient,
)

from app.application.ingestion.contracts.download_dispatcher import (
    DownloadDispatcher,
)


class AzureServiceBusDownloadDispatcher(
    DownloadDispatcher,
):

    def __init__(
        self,
        connection_string: str,
        queue_name: str,
    ):
        self.connection_string = (
            connection_string
        )

        self.queue_name = (
            queue_name
        )

    async def dispatch(
        self,
        document_id: UUID,
    ):

        payload = {
            "document_id": str(
                document_id,
            ),
        }
        
        print("in ra connection string: ", self.connection_string)

        client = (
            ServiceBusClient.from_connection_string(
                self.connection_string,
            )
        )

        async with client:

            sender = (
                client.get_queue_sender(
                    queue_name=(
                        self.queue_name
                    ),
                )
            )

            async with sender:

                await sender.send_messages(
                    ServiceBusMessage(
                        json.dumps(
                            payload,
                        ),
                    ),
                )