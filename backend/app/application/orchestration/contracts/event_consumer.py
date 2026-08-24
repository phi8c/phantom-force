from abc import ABC
from abc import abstractmethod


class EventConsumer(
    ABC,
):

    @abstractmethod
    async def receive_messages(
        self,
    ) -> list[dict]:
        pass