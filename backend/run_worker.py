import argparse
import asyncio

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


async def run_worker(worker_name: str) -> None:
    queues = create_ingest_queue_clients()
    dispatchers = create_ingest_dispatchers(queues)

    if worker_name == "discovery":
        # TODO: replace with the concrete resolver used by
        # this runtime.
        from integration.ingest.discovery.data_hub_discovery_provider_resolver import (
            DataHubProviderResolver,
        )

        worker = create_discovery_worker(
            queues=queues,
            dispatchers=dispatchers,
            data_hub_provider_resolver=DataHubProviderResolver(),
        )

    elif worker_name == "download":
        # TODO: use the concrete adapters currently configured
        # for this project.
        from integration.ingest.download.data_hub_document_source import (
            DataHubDocumentSource,
        )
        from integration.ingest.download.file_storage_object_storage import (
            FileStorageObjectStorage,
        )

        worker = create_download_worker(
            queues=queues,
            dispatchers=dispatchers,
            document_source=DataHubDocumentSource(),
            object_storage=FileStorageObjectStorage(),
        )

    elif worker_name == "extraction":
        from module.data_platform.file_storage.composition.factory import (
            create_supabase_file_storage,
        )

        file_storage = create_supabase_file_storage()

        worker = create_extraction_worker(
            queues=queues,
            dispatchers=dispatchers,
            file_storage=file_storage,
            object_storage=file_storage,
        )

    elif worker_name == "chunking":
        from module.data_platform.file_storage.composition import (
            create_file_storage,
        )

        worker = create_chunking_worker(
            queues=queues,
            dispatchers=dispatchers,
            file_storage=create_file_storage(),
        )

    elif worker_name == "embedding":
        worker = create_embedding_worker(
            queues=queues,
        )

    elif worker_name == "classification":
        worker = create_classification_worker(
            queues=queues,
        )

    else:
        raise ValueError(
            f"Unknown worker: {worker_name}"
        )

    try:
        await worker.run()
    finally:
        await close_ingest_queue_clients(
            queues,
        )


def main() -> None:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "worker",
        choices=[
            "discovery",
            "download",
            "extraction",
            "chunking",
            "embedding",
            "classification",
        ],
    )

    args = parser.parse_args()

    asyncio.run(
        run_worker(args.worker)
    )


if __name__ == "__main__":
    main()
