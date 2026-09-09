import asyncio
import logging

from bootstrap.queues import (
    close_ingest_queue_clients,
    create_ingest_dispatchers,
    create_ingest_queue_clients,
)
from bootstrap.workers import (
    create_chunking_worker,
    create_classification_worker,
    create_discovery_worker,
    create_download_worker,
    create_embedding_worker,
    create_extraction_worker,
)
from run_worker import (
    configure_worker_logging,
    create_data_hub_provider_resolver,
    create_download_document_source,
    create_download_object_storage,
    create_extraction_object_storage,
    create_file_storage,
    create_graph_token_provider,
    get_storage_provider_id,
)


logger = logging.getLogger(__name__)


async def run() -> None:
    configure_worker_logging()

    logger.info("local ingest bootstrap starting")

    # Một bộ queue client dùng chung cho toàn process.
    queues = create_ingest_queue_clients()
    dispatchers = create_ingest_dispatchers(queues)

    # Các dependency có thể share giữa nhiều worker.
    file_storage = create_file_storage()
    storage_provider_id = await get_storage_provider_id()

    token_provider = create_graph_token_provider()
    data_hub_provider_resolver = (
        create_data_hub_provider_resolver()
    )

    workers = [
        create_discovery_worker(
            queues=queues,
            dispatchers=dispatchers,
            data_hub_provider_resolver=(
                data_hub_provider_resolver
            ),
        ),
        create_download_worker(
            queues=queues,
            dispatchers=dispatchers,
            document_source=(
                create_download_document_source(
                    token_provider,
                )
            ),
            object_storage=(
                create_download_object_storage(
                    file_storage,
                    storage_provider_id,
                )
            ),
        ),
        create_extraction_worker(
            queues=queues,
            dispatchers=dispatchers,
            file_storage=file_storage,
            object_storage=(
                create_extraction_object_storage(
                    file_storage,
                    storage_provider_id,
                )
            ),
        ),
        create_chunking_worker(
            queues=queues,
            dispatchers=dispatchers,
            file_storage=file_storage,
        ),
        create_embedding_worker(
            queues=queues,
        ),
        create_classification_worker(
            queues=queues,
            file_storage=file_storage,
        ),
    ]

    logger.info(
        "local ingest starting workers=%s",
        len(workers),
    )

    try:
        await asyncio.gather(
            *(worker.run() for worker in workers)
        )

    finally:
        logger.info(
            "local ingest shutting down"
        )

        await close_ingest_queue_clients(
            queues,
        )


def main() -> None:
    asyncio.run(run())


if __name__ == "__main__":
    main()