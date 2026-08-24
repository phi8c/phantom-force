from app.application.commands.run_classification_command import (
    RunClassificationCommand,
)
from app.shared.logging.logger import logger


class RunClassificationCommandHandler:
    """
    Handle RunClassificationCommand.
    """

    async def handle(
        self,
        command: RunClassificationCommand,
    ) -> None:

        logger.info(
            "Processing classification command. document_id=%s",
            command.document_id,
        )

        #
        # Sprint 3
        #
        # await classification_service.execute(command)
        #

        logger.info(
            "Classification command processed successfully. document_id=%s",
            command.document_id,
        )