from app.domain.repositories.source_repository import (
    SourceRepository,
)

from app.application.source.responses.source_response import (
    SourceResponse,
)


class GetSourcesUseCase:
    def __init__(
        self,
        source_repository: SourceRepository,
    ):
        self.source_repository = source_repository

    async def execute(
        self,
    ) -> list[SourceResponse]:

        sources = (
            await self.source_repository.get_enabled_sources()
        )

        return [
            SourceResponse(
                id=source.id,
                name=source.name,
                source_type=source.source_type,
                site_id=source.site_id,
                enabled=source.enabled,
            )
            for source in sources
        ]