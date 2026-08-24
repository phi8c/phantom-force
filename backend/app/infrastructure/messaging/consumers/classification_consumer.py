from app.application.commands.base_command import BaseCommand
from app.application.commands.run_classification_command import (
    RunClassificationCommand,
)
from app.application.orchestration.handlers.run_classification_command_handler import (
    RunClassificationCommandHandler,
)
from app.infrastructure.messaging.consumers.base_consumer import (
    BaseConsumer,
)
from app.shared.config import settings


class ClassificationConsumer(BaseConsumer):
    """
    Consumer responsible for processing classification commands.
    """

    queue_name = settings.CLASSIFICATION_QUEUE_NAME

    def __init__(self) -> None:
        super().__init__()

        self._handler = RunClassificationCommandHandler()

    async def handle(
        self,
        command: BaseCommand,
    ) -> None:

        if not isinstance(command, RunClassificationCommand):
            raise TypeError(
                f"Expected RunClassificationCommand, got {type(command).__name__}"
            )

        await self._handler.handle(command)