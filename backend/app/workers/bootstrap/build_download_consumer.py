from app.shared.config.settings import (
    settings,
)

from app.domain.ports.storage.extract.supabase.supabase_storage import (
    SupabaseStorage,
)

from app.infrastructure.messaging.azure.azure_service_bus_extract_dispatcher import (
    AzureServiceBusExtractDispatcher,
)

from app.infrastructure.providers.datasource.sharepoint.sharepoint_document_source import (
    SharePointDocumentSource,
)

from app.infrastructure.providers.storage.local_temp_storage import (
    LocalTempStorage,
)

from app.presentation.source.dependencies.source_dependencies import (
    get_sharepoint_service,
)

from app.workers.consumers.download_consumer import (
    DownloadConsumer,
)

from app.workers.workers.download_worker import (
    DownloadWorker,
)


def build_download_consumer():

    sharepoint_service = (
        get_sharepoint_service()
    )

    document_source = (
        SharePointDocumentSource(
            sharepoint_service,
        )
    )

    temp_storage = (
        LocalTempStorage()
    )

    original_file_storage = (
        SupabaseStorage()
    )

    extract_dispatcher = (
        AzureServiceBusExtractDispatcher(
            connection_string=(
                settings.AZURE_SERVICE_BUS_CONNECTION_STRING
            ),
            queue_name=(
                settings.AZURE_SERVICE_BUS_EXTRACT_QUEUE
            ),
        )
    )

    download_worker = (
        DownloadWorker(
            document_source=document_source,
            temp_storage=temp_storage,
            storage=original_file_storage,
            extract_dispatcher=extract_dispatcher,
        )
    )

    return DownloadConsumer(
        connection_string=(
            settings.AZURE_SERVICE_BUS_CONNECTION_STRING
        ),
        queue_name=(
            settings.AZURE_SERVICE_BUS_QUEUE_NAME
        ),
        download_worker=download_worker,
    )