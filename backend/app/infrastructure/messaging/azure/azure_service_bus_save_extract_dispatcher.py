import json

from azure.servicebus import (
    ServiceBusMessage,
)

from azure.servicebus.aio import (
    ServiceBusClient,
)


class AzureServiceBusSaveExtractionDispatcher:

    def __init__(
        self,
        connection_string,
        queue_name,
    ):
        self.connection_string = (
            connection_string
        )

        self.queue_name = (
            queue_name
        )

    async def dispatch(
        self,
        message,
    ):

        client = (
            ServiceBusClient
            .from_connection_string(
                self.connection_string,
            )
        )

        async with client:

            sender = (
                client.get_queue_sender(
                    queue_name=(
                        self.queue_name
                    )
                )
            )

            async with sender:

                await sender.send_messages(
                    ServiceBusMessage(
                        json.dumps(
                            {
                                "document_id": str(
                                    message.document_id
                                ),
                                "extraction": (
                                    message.extraction
                                ),
                            }
                        )
                    )
                )