from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.persistence.session import (
    get_session,
)

from app.infrastructure.persistence.repositories.source_repository_impl import (
    SourceRepositoryImpl,
)

from app.infrastructure.persistence.unit_of_work import (
    SqlAlchemyUnitOfWork,
)

from app.infrastructure.providers.datasource.sharepoint.azure_ad_token_provider import (
    AzureAdTokenProvider,
)

from app.infrastructure.providers.datasource.sharepoint.graph_http_client import (
    GraphHttpClient,
)

from app.infrastructure.providers.datasource.sharepoint.sharepoint_gateway_impl import (
    SharePointGatewayImpl,
)

from app.infrastructure.providers.datasource.sharepoint.sharepoint_service import (
    SharePointService,
)

from app.shared.config.settings import (
    settings,
)

from fastapi import Depends

from app.infrastructure.providers.datasource.sharepoint.sharepoint_service import (
    SharePointService,
)

from app.infrastructure.providers.datasource.sharepoint.sharepoint_document_source import (
    SharePointDocumentSource,
)


def get_sharepoint_service() -> SharePointService:

    return SharePointService()


def get_document_source(
    sharepoint_service: SharePointService = Depends(
        get_sharepoint_service,
    ),
):

    return SharePointDocumentSource(
        sharepoint_service,
    )


def get_source_repository(
    session: AsyncSession = Depends(
        get_session,
    ),
):
    return SourceRepositoryImpl(
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


def get_sharepoint_service():

    token_provider = (
        AzureAdTokenProvider()
    )

    graph_client = (
        GraphHttpClient(
            token_provider=token_provider,
            base_url=settings.GRAPH_BASE_URL,
        )
    )

    gateway = (
        SharePointGatewayImpl(
            graph_client,
        )
    )

    return SharePointService(
        gateway,
    )