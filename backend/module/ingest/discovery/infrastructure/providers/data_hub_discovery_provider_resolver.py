import logging

from module.data_platform.data_hub.composition import (
    DataHubProviderRegistry,
)
from module.data_platform.data_hub.shared.domain.value_objects.source_reference import (
    SourceReference as DataHubSourceReference,
)
from module.ingest.discovery.domain.contracts.discovery_provider import (
    DiscoveredFile,
    DiscoveryPage,
    DiscoveryProvider,
    SourceReference,
)
from module.ingest.discovery.domain.contracts.discovery_provider_resolver import (
    DiscoveryProviderResolver,
)


logger = logging.getLogger(__name__)


class DataHubDiscoveryProviderResolver(
    DiscoveryProviderResolver,
):

    def __init__(
        self,
        data_hub_provider_resolver: DataHubProviderRegistry,
    ):
        self._data_hub_provider_resolver = (
            data_hub_provider_resolver
        )

    def resolve(
        self,
        *,
        provider: str,
        configuration: dict | None = None,
    ) -> DiscoveryProvider:

        logger.info(
            "data_hub discovery_provider_resolving provider=%s",
            provider,
        )

        try:
            data_hub_provider = self._data_hub_provider_resolver.resolve(
                provider=provider,
                configuration=configuration,
            )
        except Exception:
            logger.exception(
                "data_hub discovery_provider_resolve_failed provider=%s",
                provider,
            )
            raise

        logger.info(
            "data_hub discovery_provider_resolved provider=%s implementation=%s",
            provider,
            type(data_hub_provider).__name__,
        )

        return DataHubDiscoveryProvider(
            data_hub_provider.discovery,
        )


class DataHubDiscoveryProvider(
    DiscoveryProvider,
):

    def __init__(
        self,
        discovery_provider,
    ):
        self._discovery_provider = discovery_provider

    async def discover(
        self,
        source: SourceReference,
        *,
        cursor: dict | None = None,
        limit: int = 100,
    ) -> DiscoveryPage:

        logger.info(
            "data_hub discovery_start provider=%s source_id=%s limit=%s has_cursor=%s",
            source.provider,
            source.identifier,
            limit,
            cursor is not None,
        )

        page = await self._discovery_provider.discover(
            source=DataHubSourceReference(
                provider=source.provider,
                identifier=source.identifier,
                metadata=source.metadata,
            ),
            cursor=cursor,
            limit=limit,
        )

        logger.info(
            "data_hub discovery_done provider=%s source_id=%s items=%s has_more=%s",
            source.provider,
            source.identifier,
            len(page.items),
            page.has_more,
        )

        return DiscoveryPage(
            items=[
                DiscoveredFile(
                    external_file_id=(
                        item.external_file_id
                    ),
                    file_name=item.file_name,
                    file_extension=(
                        item.file_extension
                    ),
                    file_size_bytes=(
                        item.file_size_bytes
                    ),
                    source_file_url=(
                        item.source_file_url
                    ),
                    provider_metadata=dict(
                        item.provider_metadata
                        or {}
                    ),
                    last_modified_at=(
                        item.last_modified_at
                    ),
                    original_file_path=(
                        item.original_file_path
                    ),
                )
                for item in page.items
            ],
            next_cursor=page.next_cursor,
            has_more=page.has_more,
        )
