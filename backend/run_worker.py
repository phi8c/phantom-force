import argparse
import asyncio
import logging
from collections.abc import AsyncIterator
from uuid import UUID

from bootstrap.database import async_session_factory
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
from module.data_platform.common.microsoft_graph.authentication.token_provider import (
    TokenProvider,
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


class ClientSecretGraphTokenProvider(TokenProvider):

    def __init__(
        self,
        *,
        tenant_id: str,
        client_id: str,
        client_secret: str,
        scope: str,
    ) -> None:
        self._tenant_id = tenant_id
        self._client_id = client_id
        self._client_secret = client_secret
        self._scope = scope

    async def get_token(self) -> str:
        import httpx

        url = (
            "https://login.microsoftonline.com/"
            f"{self._tenant_id}/oauth2/v2.0/token"
        )

        async with httpx.AsyncClient(
            timeout=30.0,
        ) as client:
            response = await client.post(
                url,
                data={
                    "client_id": self._client_id,
                    "client_secret": self._client_secret,
                    "scope": self._scope,
                    "grant_type": "client_credentials",
                },
            )

            response.raise_for_status()

            return str(
                response.json()["access_token"]
            )


def create_graph_token_provider() -> TokenProvider:
    required = {
        "GRAPH_TENANT_ID": settings.GRAPH_TENANT_ID,
        "GRAPH_CLIENT_ID": settings.GRAPH_CLIENT_ID,
        "GRAPH_CLIENT_SECRET": (
            settings.GRAPH_CLIENT_SECRET
        ),
        "GRAPH_SCOPE": settings.GRAPH_SCOPE,
    }
    missing = [
        name
        for name, value in required.items()
        if not value
    ]

    if missing:
        raise RuntimeError(
            "Missing Microsoft Graph settings: "
            + ", ".join(missing)
        )

    return ClientSecretGraphTokenProvider(
        tenant_id=settings.GRAPH_TENANT_ID,
        client_id=settings.GRAPH_CLIENT_ID,
        client_secret=settings.GRAPH_CLIENT_SECRET,
        scope=settings.GRAPH_SCOPE,
    )


def create_data_hub_provider_resolver():
    from module.data_platform.data_hub.composition.provider_resolver import (
        DataHubProviderResolver,
    )

    return DataHubProviderResolver(
        token_provider=create_graph_token_provider(),
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


def create_download_stream_factory(
    token_provider: TokenProvider,
):

    def stream_factory(
        document,
    ) -> AsyncIterator[bytes]:
        provider_name = str(
            document.provider_metadata.get(
                "provider",
                "sharepoint",
            )
        )

        async def stream() -> AsyncIterator[bytes]:
            if provider_name.strip().lower() != "sharepoint":
                raise ValueError(
                    "Unsupported download provider: "
                    f"{provider_name}"
                )

            from module.data_platform.common.microsoft_graph.client import (
                MicrosoftGraphClient,
            )
            from module.data_platform.data_hub.infrastructure.providers.sharepoint.downloader import (
                SharePointFileDownloader,
            )
            from module.data_platform.data_hub.domain.entities.discovered_file import (
                DiscoveredFile,
            )
            from module.data_platform.data_hub.domain.value_objects.source_reference import (
                SourceReference,
            )

            graph_client = MicrosoftGraphClient(
                token_provider=token_provider,
                base_url=settings.GRAPH_BASE_URL,
            )

            try:
                file = DiscoveredFile(
                    external_file_id=str(
                        document.provider_metadata.get(
                            "external_file_id",
                            document.id,
                        )
                    ),
                    file_name=document.file_name,
                    file_extension=document.file_extension,
                    file_size_bytes=document.file_size_bytes,
                    source_file_url=document.source_file_url,
                    source=SourceReference(
                        provider=provider_name,
                        identifier=str(document.id),
                        metadata=document.provider_metadata,
                    ),
                    provider_metadata=document.provider_metadata,
                    last_modified_at=None,
                    original_file_path=None,
                )

                downloader = SharePointFileDownloader(
                    graph_client,
                )

                async for chunk in downloader.download_stream(
                    file,
                ):
                    yield chunk

            finally:
                await graph_client.close()

        return stream()

    return stream_factory


def create_download_document_source(
    token_provider: TokenProvider,
):
    from integration.ingest.download.data_hub_document_source import (
        DataHubDocumentSource,
    )
    from module.ingest.download.infrastructure.persistence.readers.download_document_reader_impl import (
        DownloadDocumentReaderImpl,
    )

    class RuntimeDownloadDocumentSource:

        async def open(
            self,
            document_id: UUID,
        ):
            async with async_session_factory() as session:
                source = DataHubDocumentSource(
                    document_reader=DownloadDocumentReaderImpl(
                        session=session,
                    ),
                    stream_factory=create_download_stream_factory(
                        token_provider,
                    ),
                )

                return await source.open(
                    document_id,
                )

    return RuntimeDownloadDocumentSource()


def create_download_object_storage(
    file_storage,
    storage_provider_id: UUID,
):
    from integration.ingest.download.file_storage_object_storage import (
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
    from integration.ingest.extraction.file_storage_object_storage import (
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
    queues = create_ingest_queue_clients()
    dispatchers = create_ingest_dispatchers(queues)

    try:
        if worker_name == "discovery":
            logger.info("worker creating name=discovery")
            data_hub_provider_resolver = (
                create_data_hub_provider_resolver()
            )

            worker = create_discovery_worker(
                queues=queues,
                dispatchers=dispatchers,
                data_hub_provider_resolver=(
                    data_hub_provider_resolver
                ),
            )

        elif worker_name == "download":
            logger.info("worker creating name=download")
            token_provider = create_graph_token_provider()
            file_storage = create_file_storage()
            storage_provider_id = (
                await get_storage_provider_id()
            )

            worker = create_download_worker(
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
            )

        elif worker_name == "extraction":
            logger.info("worker creating name=extraction")
            file_storage = create_file_storage()
            storage_provider_id = (
                await get_storage_provider_id()
            )

            worker = create_extraction_worker(
                queues=queues,
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
                queues=queues,
                dispatchers=dispatchers,
                file_storage=file_storage,
            )

        elif worker_name == "embedding":
            logger.info("worker creating name=embedding")
            worker = create_embedding_worker(
                queues=queues,
            )

        elif worker_name == "classification":
            logger.info("worker creating name=classification")
            worker = create_classification_worker(
                queues=queues,
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
