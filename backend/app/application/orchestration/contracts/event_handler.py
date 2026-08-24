from abc import ABC
from abc import abstractmethod

from app.domain.events.base_event import (
    BaseEvent,
)


class EventHandler(
    ABC,
):

    @abstractmethod
    async def handle(
        self,
        event: BaseEvent,
    ) -> None:
        pass