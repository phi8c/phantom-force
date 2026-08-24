from abc import ABC
from abc import abstractmethod

class EventPublisher(ABC):

    @abstractmethod
    async def publish(
        self,
        event,
    ):
        pass