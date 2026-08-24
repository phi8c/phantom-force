from abc import ABC
from abc import abstractmethod

from app.application.commands.base_command import BaseCommand


class CommandBus(ABC):

    @abstractmethod
    async def publish(
        self,
        command: BaseCommand,
    ) -> None:
        ...