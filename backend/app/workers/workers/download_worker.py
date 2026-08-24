from app.domain.repositories.document_repository import (
    DocumentRepository,
)


class DownloadWorker:

    def __init__(
        self,
        document_source,
        temp_storage,
        storage,
        extract_dispatcher,
    ):
        self.document_source = (
            document_source
        )

        self.temp_storage = (
            temp_storage
        )

        self.original_file_storage = (
            storage
        )

        self.extract_dispatcher = (
            extract_dispatcher
        )

    async def execute(
        self,
        document,
        document_repository: DocumentRepository,
        uow,
    ):

        print("1. Download SharePoint")

        content = await (
    self.document_source.download_file(
        provider_metadata=document.provider_metadata,
        external_file_id=document.external_file_id,
    )
)

        print("   Bytes:", len(content))

        temp_path = await (
            self.temp_storage.save(
                file_name=(
                    f"{document.id}"
                    f".{document.file_extension}"
                ),
                content=content,
            )
        )

        print("3. Upload Supabase")

        storage_path = await (
            self.original_file_storage.upload_original(
                document_id=str(
                    document.id
                ),
                file_name=(
                    f"{document.id}"
                    f".{document.file_extension}"
                ),
                content=content,
            )
        )

        print(storage_path)

        document.temp_file_path = (
            temp_path
        )

        print("4. Update document")

        document.original_file_path = (
            storage_path
        )

        await (
            document_repository.update(
                document,
            )
        )

        print("5. Commit")

        await uow.commit()

        print("6. Dispatch Extract")

        await (
            self.extract_dispatcher.dispatch(
                document.id,
            )
        )

        print("7. Finished")