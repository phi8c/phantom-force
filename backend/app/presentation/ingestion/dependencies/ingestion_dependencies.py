from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.persistence.session import (
    get_session,
)

from app.infrastructure.persistence.unit_of_work import (
    SqlAlchemyUnitOfWork,
)

from app.infrastructure.persistence.repositories.ingestion_run_repository_impl import (
    IngestionRunRepositoryImpl,
)

from app.infrastructure.persistence.repositories.document_repository_impl import (
    DocumentRepositoryImpl,
)

from app.infrastructure.persistence.repositories.document_extraction_repository_impl import (
    DocumentExtractionRepositoryImpl,
)

from app.infrastructure.providers.extraction.docling.docling_extractor import (
    DoclingExtractor,
)

from app.infrastructure.providers.datasource.sharepoint.sharepoint_document_source import (
    SharePointDocumentSource,
)

from app.presentation.source.dependencies.source_dependencies import (
    get_sharepoint_service,
)
from app.infrastructure.messaging.azure.azure_service_bus_download_dispatcher import (
    AzureServiceBusDownloadDispatcher,
)



from app.shared.config.settings import (settings,
)



def get_ingestion_planner():

    sharepoint_service = (
        get_sharepoint_service()
    )

    return SharePointDocumentSource(
        sharepoint_service,
    )


def get_ingestion_run_repository(
    session: AsyncSession = Depends(
        get_session,
    ),
):
    return IngestionRunRepositoryImpl(
        session,
    )


def get_uow(
    session: AsyncSession = Depends(
        get_session,
    ),
):
    return SqlAlchemyUnitOfWork(
        session,
    )


def get_document_source():

    sharepoint_service = (
        get_sharepoint_service()
    )

    return SharePointDocumentSource(
        sharepoint_service,
    )


def get_document_repository(
    session: AsyncSession = Depends(
        get_session,
    ),
):
    return DocumentRepositoryImpl(
        session,
    )


def get_document_extraction_repository(
    session: AsyncSession = Depends(
        get_session,
    ),
):
    return (
        DocumentExtractionRepositoryImpl(
            session,
        )
    )


def get_document_extractor():

    return (
        DoclingExtractor()
    )
def get_download_dispatcher():

    return (
        AzureServiceBusDownloadDispatcher(
            connection_string=(
                settings.AZURE_SERVICE_BUS_CONNECTION_STRING
            ),
            queue_name=(
                settings.AZURE_SERVICE_BUS_QUEUE_NAME
            ),
        )
    )
