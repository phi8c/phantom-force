from app.application.orchestration.event_dispatcher import (
    EventDispatcher,
)

from app.application.orchestration.event_resolver import (
    EventResolver,
)
from app.application.orchestration.event_deserializer import (
    EventDeserializer,
)


class EventProcessor:

    def __init__(
        self,
        resolver: EventResolver,
        dispatcher: EventDispatcher,
        deserializer: EventDeserializer,
    ):
        self.resolver = (
            resolver
        )

        self.dispatcher = (
            dispatcher
        )

        self.deserializer = (
            deserializer
        )

    async def process(
        self,
        payload: dict,
    ) -> None:

        event_type = (
            payload[
                "event_type"
            ]
        )

        event_class = (
            self.resolver.resolve(
                event_type,
            )
        )

        event = (
    self.deserializer.deserialize(
        event_class,
        payload["event"],
    )
)
        await (
            self.dispatcher.dispatch(
                event,
            )
        )