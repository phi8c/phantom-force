# app/infrastructure/messaging/azure/azure_service_bus_event_publisher.py

import json

from azure.servicebus.aio import (
    ServiceBusClient,
)

from azure.servicebus import (
    ServiceBusMessage,
)

from app.application.orchestration.event_publisher import (
    EventPublisher,
)


class AzureServiceBusEventPublisher(
    EventPublisher,
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

    async def publish(
        self,
        event,
    ):

        payload = {
            "event_type": (
                type(event).__name__
            ),
            "event": (
                event.to_dict()
            ),
        }

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
                    )
                )
            )

            async with sender:

                await sender.send_messages(
                    ServiceBusMessage(
                        json.dumps(
                            payload,
                        )
                    )
                )