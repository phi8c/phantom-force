from __future__ import annotations

from collections.abc import AsyncIterator
import logging
from uuid import UUID

from bootstrap.database import async_session_factory
from module.data_platform.data_hub.composition import (
    create_data_hub_downloader_registry,
)
from module.data_platform.data_hub.composition import (
    create_data_hub_provider_resolver as create_neutral_provider_resolver,
)
from module.data_platform.data_hub.composition import (
    open_data_hub_download_stream,
)
from module.data_platform.data_hub.shared.domain.entities.discovered_file import (
    DiscoveredFile,
)
from module.data_platform.data_hub.shared.domain.value_objects.source_reference import (
    SourceReference,
)
from module.ingest.config.infrastructure.persistence.repositories.ingestion_config_repository_impl import (
    IngestionConfigRepositoryImpl,
)
from module.ingest.download.infrastructure.persistence.readers.download_document_reader_impl import (
    DownloadDocumentReaderImpl,
)
from module.ingest.download.infrastructure.sources.data_hub_document_source import (
    DataHubDocumentSource,
)
from module.knowledge_space.application.services.data_hub_configuration_resolver import (
    KnowledgeSpaceDataHubConfigurationResolver,
    ResolvedDataHubConfiguration,
)
from module.knowledge_space.infrastructure.persistence.repositories.knowledge_space_data_hub_repository_impl import (
    KnowledgeSpaceDataHubRepositoryImpl,
)
from module.master_data.data_hub_providers.infrastructure.persistence.repositories.data_hub_provider_repository_impl import (
    DataHubProviderRepositoryImpl,
)


logger = logging.getLogger(__name__)


def create_data_hub_provider_resolver():
    return create_neutral_provider_resolver()


def create_download_stream_factory(
    *,
    resolved: ResolvedDataHubConfiguration,
    registry,
):
    def stream_factory(document) -> AsyncIterator[bytes]:
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
                provider=resolved.provider,
                identifier=str(document.id),
                metadata=document.provider_metadata,
            ),
            provider_metadata=document.provider_metadata,
            last_modified_at=None,
            original_file_path=(
                document.provider_metadata.get("path_display")
                or document.provider_metadata.get("path_lower")
            ),
        )
        return open_data_hub_download_stream(
            registry=registry,
            provider=resolved.provider,
            configuration=resolved.configuration,
            file=file,
        )

    return stream_factory


def create_download_document_source():
    downloader_registry = create_data_hub_downloader_registry()

    class RuntimeDownloadDocumentSource:
        async def open(
            self,
            document_id: UUID,
            *,
            ingestion_job_id: UUID,
        ):
            async with async_session_factory() as session:
                job = await IngestionConfigRepositoryImpl(
                    session
                ).get_job_by_id(ingestion_job_id)
                if job is None:
                    raise LookupError(
                        f"Ingestion job '{ingestion_job_id}' was not found."
                    )

                resolved = await KnowledgeSpaceDataHubConfigurationResolver(
                    KnowledgeSpaceDataHubRepositoryImpl(session),
                    DataHubProviderRepositoryImpl(session),
                ).resolve(job.knowledge_space_id)
                logger.info(
                    "download data_hub_resolved job_id=%s document_id=%s knowledge_space_id=%s data_hub_id=%s provider=%s config_keys=%s",
                    ingestion_job_id,
                    document_id,
                    job.knowledge_space_id,
                    resolved.data_hub_id,
                    resolved.provider,
                    sorted(resolved.configuration.keys()),
                )

                source = DataHubDocumentSource(
                    document_reader=DownloadDocumentReaderImpl(
                        session=session,
                    ),
                    stream_factory=create_download_stream_factory(
                        resolved=resolved,
                        registry=downloader_registry,
                    ),
                )
                return await source.open(
                    document_id,
                    ingestion_job_id=ingestion_job_id,
                )

    return RuntimeDownloadDocumentSource()


__all__ = [
    "create_data_hub_provider_resolver",
    "create_download_document_source",
    "create_download_stream_factory",
]
