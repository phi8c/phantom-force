from app.application.classification.engine import (
    ClassificationEngine,
)

from app.workers.host.classification_host import (
    ClassificationHost,
)

from app.workers.workers.classification_worker import (
    ClassificationWorker,
)


def build_classification_host() -> ClassificationHost:

    classification_engine = (
        ClassificationEngine()
    )

    classification_worker = (
        ClassificationWorker(
            classification_engine=classification_engine,
        )
    )

    return ClassificationHost(
        classification_worker=classification_worker,
    )