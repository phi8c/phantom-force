import asyncio

from app.application.orchestration.event_registry import (
    EventRegistry,
)

from app.domain.events.base_event import (
    BaseEvent,
)


class EventDispatcher:

    def __init__(
        self,
        registry: EventRegistry,
    ):
        self.registry = registry

    async def dispatch(
        self,
        event: BaseEvent,
    ) -> None:

        handlers = (
            self.registry.get_handlers(
                type(event),
            )
        )

        await asyncio.gather(
            *[
                handler.handle(
                    event,
                )
                for handler in handlers
            ]
        )