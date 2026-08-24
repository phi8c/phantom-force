from abc import ABC
from abc import abstractmethod

from app.domain.events.base_event import (
    BaseEvent,
)


class MessageBus(
    ABC,
):

    @abstractmethod
    async def publish_task(
        self,
        task_id: str,
        task_type: str,
    ) -> None:
        pass

    @abstractmethod
    async def publish_event(
        self,
        event: BaseEvent,
    ) -> None:
        pass