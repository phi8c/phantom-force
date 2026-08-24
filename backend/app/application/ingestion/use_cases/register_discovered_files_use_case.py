from app.domain.entities.document import (
    Document,
)


class RegisterDiscoveredFilesUseCase:

    def __init__(
        self,
        document_repository,
        uow,
    ):
        self.document_repository = (
            document_repository
        )

        self.uow = uow

    async def execute(
        self,
        source_id,
        files,
    ):

        documents = []

        for file in files:

            existing = await (
                self.document_repository
                .get_by_external_file_id(
                    source_id,
                    file.external_file_id,
                )
            )

            if existing:

                documents.append(
                    existing,
                )

                continue

            document = Document(
                id=None,
                source_id=source_id,
                external_file_id=(
                    file.external_file_id
                ),
                provider_metadata=(
                    file.provider_metadata
                ),
                file_name=file.file_name,
                department=None,
                owner_role=None,
                security_level=None,
                document_type=None,
                source_file_url=(
                    file.source_file_url
                ),
                file_extension=(
                    file.file_extension
                ),
                file_size_bytes=(
                    file.file_size_bytes
                ),
                content_hash=None,
                processing_status=(
                    "PENDING_DOWNLOAD"
                ),
                processing_error=None,
                temp_file_path=None,
                last_modified_at=(
                    file.last_modified_at
                ),
                last_ingested_at=None,
                created_at=None,
                updated_at=None,
            )

            document = await (
                self.document_repository
                .create(
                    document,
                )
            )

            documents.append(
                document,
            )

        await self.uow.commit()

        return documents