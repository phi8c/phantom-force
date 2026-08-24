from app.application.orchestration.contracts.event_consumer import (
    EventConsumer,
)

from app.application.orchestration.event_processor import (
    EventProcessor,
)


class EventRuntime:

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

            if not payloads:
                continue

            for payload in payloads:

                try:

                    await (
                        self.processor.process(
                            payload,
                        )
                    )

                except Exception as ex:

                    print(
                        "Event processing failed:",
                        ex,
                    )