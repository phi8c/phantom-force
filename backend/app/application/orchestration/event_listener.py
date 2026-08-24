from app.application.orchestration.event_processor import (
    EventProcessor,
)

from app.application.orchestration.contracts.event_consumer import (
    EventConsumer,
)


class EventListener:

    def __init__(
        self,
        consumer: EventConsumer,
        processor: EventProcessor,
    ):
        self.consumer = (
            consumer
        )

        self.processor = (
            processor
        )

    async def start(
        self,
    ) -> None:

        while True:

            payloads = await (
                self.consumer.receive_messages()
            )

            for payload in payloads:

                await (
                    self.processor.process(
                        payload,
                    )
                )