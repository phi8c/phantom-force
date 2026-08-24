from app.workers.consumers.classification_consumer import (
    ClassificationConsumer,
)

from app.workers.workers.classification_worker import (
    ClassificationWorker,
)


class ClassificationHost:

    def __init__(
        self,
        classification_worker: ClassificationWorker,
    ) -> None:

        self._consumer = (
            ClassificationConsumer(
                classification_worker=classification_worker,
            )
        )

    async def start(
        self,
    ) -> None:

        await self._consumer.start()