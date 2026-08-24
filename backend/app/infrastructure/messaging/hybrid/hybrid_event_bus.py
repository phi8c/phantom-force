from app.application.orchestration.contracts.event_bus import (
    EventBus,
)

from app.domain.events.base_event import (
    BaseEvent,
)


class HybridEventBus(
    EventBus,
):

    def __init__(
        self,
        local_bus: EventBus,
        distributed_bus: EventBus,
    ):
        self.local_bus = local_bus

        self.distributed_bus = (
            distributed_bus
        )

    async def publish(
        self,
        event: BaseEvent,
    ) -> None:

        await self.local_bus.publish(
            event,
        )

        await (
            self.distributed_bus.publish(
                event,
            )
        )