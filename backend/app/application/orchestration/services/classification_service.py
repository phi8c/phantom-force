from app.application.commands.run_classification_command import (
    RunClassificationCommand,
)
from app.shared.logging.logger import logger


class ClassificationService:
    """
    Business service responsible for classifying a review.
    """

    async def execute(
        self,
        command: RunClassificationCommand,
    ) -> None:
        """
        Execute the classification workflow.
        """

        logger.info(
            "Starting classification workflow. document_id=%s",
            command.document_id,
        )

        #
        # Sprint 3.2
        #
        # review = await ...
        #

        #
        # Sprint 3.3
        #
        # prompt = await ...
        #

        #
        # Sprint 3.4
        #
        # model = await ...
        #

        #
        # Sprint 3.5
        #
        # response = await ...
        #

        #
        # Sprint 3.6
        #
        # save result
        #

        logger.info(
            "Classification workflow finished. document_id=%s",
            command.document_id,
        )