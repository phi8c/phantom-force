from app.application.embedding.engine import (
    EmbeddingEngine,
)

from app.workers.host.embedding_host import (
    EmbeddingHost,
)

from app.workers.workers.embedding_worker import (
    EmbeddingWorker,
)


def build_embedding_host() -> EmbeddingHost:

    embedding_engine = (
        EmbeddingEngine()
    )

    embedding_worker = (
        EmbeddingWorker(
            embedding_engine=embedding_engine,
        )
    )

    return EmbeddingHost(
        embedding_worker=embedding_worker,
    )