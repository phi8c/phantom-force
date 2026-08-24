import json

from azure.servicebus.aio import (
    ServiceBusClient,
)

from app.application.orchestration.contracts.event_consumer import (
    EventConsumer,
)


class ServiceBusConsumer(
    EventConsumer,
):

    def __init__(
        self,
        connection_string: str,
        topic_name: str,
        subscription_name: str,
    ):
        self.connection_string = (
            connection_string
        )

        self.topic_name = (
            topic_name
        )

        self.subscription_name = (
            subscription_name
        )

    async def receive_messages(
        self,
    ) -> list[dict]:

        client = (
            ServiceBusClient
            .from_connection_string(
                self.connection_string,
            )
        )

        result: list[dict] = []

        async with client:

            receiver = (
                client.get_subscription_receiver(
                    topic_name=(
                        self.topic_name
                    ),
                    subscription_name=(
                        self.subscription_name
                    ),
                    max_wait_time=5,
                )
            )

            async with receiver:

                messages = await (
                    receiver.receive_messages(
                        max_message_count=10,
                    )
                )

                for message in messages:

                    # message.body can be bytes, bytearray or a list of bytes
                    body = message.body

                    try:
                        if isinstance(body, (bytes, bytearray)):
                            raw = body.decode("utf-8")
                        elif isinstance(body, list):
                            raw = b"".join(body).decode("utf-8")
                        else:
                            raw = str(body)

                        payload = json.loads(raw)

                    except Exception:
                        # fallback to string repr if JSON decode fails
                        payload = json.loads(str(message))

                    result.append(payload)

                    await (
                        receiver.complete_message(
                            message
                        )
                    )

        return result