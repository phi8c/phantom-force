from app.domain.events.base_event import (
    BaseEvent,
)


class EventResolver:

    def __init__(
        self,
    ):
        self._events = {}

    def register(
        self,
        event_type: str,
        event_class: type[BaseEvent],
    ) -> None:

        self._events[
            event_type
        ] = event_class

    def resolve(
        self,
        event_type: str,
    ) -> type[BaseEvent]:

        if event_type not in self._events:

            raise ValueError(
                f"Unknown event type: {event_type}"
            )

        return self._events[
            event_type
        ]