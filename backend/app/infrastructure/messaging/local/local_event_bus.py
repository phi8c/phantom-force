from app.application.orchestration.contracts.event_bus import (
    EventBus,
)

from app.application.orchestration.event_dispatcher import (
    EventDispatcher,
)

from app.domain.events.base_event import (
    BaseEvent,
)


class LocalEventBus(
    EventBus,
):

    def __init__(
        self,
        dispatcher: EventDispatcher,
    ):
        self.dispatcher = dispatcher

    async def publish(
        self,
        event: BaseEvent,
    ) -> None:

        await self.dispatcher.dispatch(
            event,
        )