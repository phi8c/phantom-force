from collections import defaultdict

from app.application.orchestration.contracts.event_handler import (
    EventHandler,
)


class EventRegistry:

    def __init__(
        self,
    ):
        self._handlers = defaultdict(
            list,
        )

    def register(
        self,
        event_type,
        handler: EventHandler,
    ) -> None:

        self._handlers[
            event_type
        ].append(
            handler,
        )

    def get_handlers(
        self,
        event_type,
    ) -> list[EventHandler]:

        return self._handlers.get(
            event_type,
            [],
        )