from module.data_platform.data_hub.composition.provider_resolver import (
    DataHubProviderResolver,
)
from module.data_platform.data_hub.domain.value_objects.source_reference import (
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


class DataHubDiscoveryProviderResolver(
    DiscoveryProviderResolver,
):

    def __init__(
        self,
        data_hub_provider_resolver: DataHubProviderResolver,
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

        data_hub_provider = (
            self._data_hub_provider_resolver
            .resolve(
                provider=provider,
                configuration=configuration,
            )
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

        page = await self._discovery_provider.discover(
            source=DataHubSourceReference(
                provider=source.provider,
                identifier=source.identifier,
                metadata=source.metadata,
            ),
            cursor=cursor,
            limit=limit,
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
