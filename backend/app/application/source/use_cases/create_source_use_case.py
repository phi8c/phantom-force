from uuid import uuid4

from app.application.source.requests.create_source_request import (
    CreateSourceRequest,
)

from app.domain.entities.ingestion_source import (
    IngestionSource,
)

from app.domain.repositories.source_repository import (
    SourceRepository,
)

from app.domain.unit_of_work.unit_of_work import (
    UnitOfWork,
)
class CreateSourceUseCase:
    def __init__(
        self, 
        source_repository: SourceRepository,
        uow: UnitOfWork,
    ):
        self.source_repository = source_repository
        self.uow = uow
    
    async def execute(
        self, 
        request: CreateSourceRequest
    ) -> IngestionSource:
        
        source = IngestionSource(
            id=uuid4(),
            name=request.name,
            source_type=request.source_type,
            site_id=request.site_id,
            drive_id=request.drive_id,
            enabled=True,
        )
        
        created_source = (
            await self.source_repository.create(
                source
            )
        )

        await self.uow.commit()

        return created_source