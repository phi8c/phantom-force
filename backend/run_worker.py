import argparse
import asyncio
import logging
from uuid import UUID

from bootstrap.database import async_session_factory
from bootstrap.data_hub import (
    create_data_hub_provider_resolver,
    create_download_document_source,
)
from bootstrap.queues import create_ingest_messaging
from bootstrap.workers import (
    create_chunking_worker,
    create_classification_worker,
    create_discovery_worker,
    create_download_worker,
    create_embedding_worker,
    create_extraction_worker,
)
from shared.config.settings import settings
from sqlalchemy import text


logger = logging.getLogger(__name__)


def configure_worker_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format=(
            "%(asctime)s | %(levelname)-5s | "
            "%(name)s | %(message)s"
        ),
    )

    for logger_name in (
        "azure",
        "azure.servicebus",
        "azure.servicebus._pyamqp",
        "azure.core.pipeline.policies.http_logging_policy",
        "uamqp",
    ):
        logging.getLogger(
            logger_name,
        ).setLevel(
            logging.WARNING,
        )


def create_file_storage():
    from module.data_platform.file_storage.composition.factory import (
        create_supabase_file_storage,
    )

    return create_supabase_file_storage(
        url=settings.SUPABASE_URL,
        key=settings.SUPABASE_KEY,
        bucket=settings.SUPABASE_STORAGE_BUCKET,
    )


async def get_storage_provider_id() -> UUID:
    logger.info("Resolving active Supabase storage provider")

    async with async_session_factory() as session:
        result = await session.execute(
            text(
                """
                SELECT id
                FROM system.storage_providers
                WHERE lower(provider_type) = 'supabase_storage'
                  AND is_active = TRUE
                ORDER BY created_at ASC
                LIMIT 1
                """
            )
        )

        row = result.mappings().one_or_none()

        if row is None:
            raise RuntimeError(
                "Active Supabase storage provider not found"
            )

        logger.info(
            "Resolved storage_provider_id=%s",
            row["id"],
        )

        return row["id"]


def create_download_object_storage(
    file_storage,
    storage_provider_id: UUID,
):
    from module.ingest.download.infrastructure.object_storage.file_storage_object_storage import (
        FileStorageObjectStorage,
    )

    return FileStorageObjectStorage(
        file_storage=file_storage,
        storage_provider_id=storage_provider_id,
    )


def create_extraction_object_storage(
    file_storage,
    storage_provider_id: UUID,
):
    from module.ingest.extraction.infrastructure.object_storage.file_storage_object_storage import (
        FileStorageObjectStorage,
    )

    return FileStorageObjectStorage(
        file_storage=file_storage,
        storage_provider_id=storage_provider_id,
    )


async def run_worker(worker_name: str) -> None:
    configure_worker_logging()
    logger.info(
        "worker bootstrap name=%s",
        worker_name,
    )
    messaging = await create_ingest_messaging()
    consumers = messaging.consumers
    dispatchers = messaging.dispatchers

    try:
        if worker_name == "discovery":
            logger.info("worker creating name=discovery")
            data_hub_provider_resolver = (
                create_data_hub_provider_resolver()
            )

            worker = create_discovery_worker(
                consumers=consumers,
                dispatchers=dispatchers,
                data_hub_provider_resolver=(
                    data_hub_provider_resolver
                ),
            )

        elif worker_name == "download":
            logger.info("worker creating name=download")
            file_storage = create_file_storage()
            storage_provider_id = (
                await get_storage_provider_id()
            )

            worker = create_download_worker(
                consumers=consumers,
                dispatchers=dispatchers,
                document_source=(
                    create_download_document_source()
                ),
                object_storage=(
                    create_download_object_storage(
                        file_storage,
                        storage_provider_id,
                    )
                ),
            )

        elif worker_name == "extraction":
            logger.info("worker creating name=extraction")
            file_storage = create_file_storage()
            storage_provider_id = (
                await get_storage_provider_id()
            )

            worker = create_extraction_worker(
                consumers=consumers,
                dispatchers=dispatchers,
                file_storage=file_storage,
                object_storage=(
                    create_extraction_object_storage(
                        file_storage,
                        storage_provider_id,
                    )
                ),
            )

        elif worker_name == "chunking":
            logger.info("worker creating name=chunking")
            file_storage = create_file_storage()

            worker = create_chunking_worker(
                consumers=consumers,
                dispatchers=dispatchers,
                file_storage=file_storage,
            )

        elif worker_name == "embedding":
            logger.info("worker creating name=embedding")
            worker = create_embedding_worker(
                consumers=consumers,
            )

        elif worker_name == "classification":
            logger.info("worker creating name=classification")
            file_storage = create_file_storage()
            worker = create_classification_worker(
                consumers=consumers,
                file_storage=file_storage,
            )

        else:
            raise ValueError(
                f"Unknown worker: {worker_name}"
            )

        logger.info(
            "worker running name=%s",
            worker_name,
        )
        await worker.run()

    except Exception:
        logger.exception(
            "worker crashed name=%s",
            worker_name,
        )
        raise

    finally:
        logger.info(
            "worker closing name=%s",
            worker_name,
        )
        await messaging.close()


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
