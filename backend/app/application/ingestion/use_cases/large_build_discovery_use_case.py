from app.domain.entities.document import (
    Document,
)

from app.domain.enums.ingestion_status import (
    IngestionStatus,
)


class LargeBuildDiscoveryUseCase:

    def __init__(
        self,
        planner,
        run_repository,
        document_repository,
        uow,
    ):
        self.planner = planner

        self.run_repository = (
            run_repository
        )

        self.document_repository = (
            document_repository
        )

        self.uow = uow

    async def execute(
        self,
        run_id,
    ):

        run = await (
            self.run_repository
            .get_by_id(
                run_id,
            )
        )

        if not run:
            raise ValueError(
                "Ingestion run not found"
            )

        run.status = (
            IngestionStatus.RUNNING
        )

        await (
            self.run_repository.update(
                run,
            )
        )

        files = await (
            self.planner
            .discover_files(
                run,
            )
        )

        total_files = 0

        for file in files:

            existing_document = await (
                self.document_repository
                .get_by_sharepoint_file_id(
                    file.file_id,
                )
            )

            if existing_document:
                continue

            document = Document(
                id=None,

                source_id=run.source_id,

                sharepoint_file_id=file.file_id,

                file_name=file.file_name,

                department=None,

                owner_role=None,

                security_level=None,

                document_type=None,

                source_file_url=file.source_file_url,

                file_extension=file.file_extension,

                file_size_bytes=file.file_size_bytes,

                content_hash=None,

                processing_status="PENDING",

                processing_error=None,

                last_modified_at=file.last_modified_at,

                last_ingested_at=None,

                created_at=None,

                updated_at=None,
            )

            await (
                self.document_repository.create(
                    document,
                )
            )

            total_files += 1

        run.total_files = total_files

        run.status = (
            IngestionStatus.COMPLETED
        )

        await (
            self.run_repository.update(
                run,
            )
        )

        await self.uow.commit()

        return {
            "run_id": str(
                run.id
            ),
            "total_files": total_files,
        }