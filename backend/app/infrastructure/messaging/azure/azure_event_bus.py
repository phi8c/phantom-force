import json
from dataclasses import asdict
from datetime import datetime
from uuid import UUID

from azure.servicebus import ServiceBusMessage
from azure.servicebus.aio import ServiceBusClient

from app.application.orchestration.contracts.event_bus import (
    EventBus,
)

from app.domain.events.base_event import (
    BaseEvent,  
)

from app.shared.config.settings import (
    settings,
)


class AzureEventBus(
    EventBus,
):

    def __init__(
        self,
    ):
        self.connection_string = (
            settings.AZURE_SERVICE_BUS_CONNECTION_STRING
        )

        self.topic_name = (
            settings.AZURE_SERVICE_BUS_QUEUE_NAME
        )

    async def publish(
        self,
        event: BaseEvent,
    ) -> None:

        payload = {
            "event_type": (
                event.__class__.__name__
            ),
            "event": (
                self._serialize_event(
                    event,
                )
            ),
        }

        client = (
            ServiceBusClient
            .from_connection_string(
                self.connection_string,
            )
        )

        async with client:

            sender = (
                client.get_topic_sender(
                    topic_name=(
                        self.topic_name
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

    def _serialize_event(
        self,
        event: BaseEvent,
    ) -> dict:

        result = {}

        for key, value in (
            asdict(event).items()
        ):

            if isinstance(
                value,
                UUID,
            ):
                result[key] = str(
                    value,
                )

            elif isinstance(
                value,
                datetime,
            ):
                result[key] = (
                    value.isoformat()
                )

            else:
                result[key] = value

        return result