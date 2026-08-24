from abc import ABC
from abc import abstractmethod

from app.domain.events.base_event import (
    BaseEvent,
)


class EventBus(
    ABC,
):

    @abstractmethod
    async def publish(
        self,
        event: BaseEvent,
    ) -> None:
        pass