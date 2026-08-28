from module.data_platform.file_storage.api import FileStorage
from module.data_platform.file_storage.application.services.file_storage_service import (
    FileStorageService,
)
from module.data_platform.file_storage.infrastructure.providers.supabase.client import (
    SupabaseClientFactory,
)
from module.data_platform.file_storage.infrastructure.providers.supabase.file_storage import (
    SupabaseFileStorage,
)


def create_supabase_file_storage(
    url: str,
    key: str,
    bucket: str,
) -> FileStorage:

    client = SupabaseClientFactory.create(
        url=url,
        key=key,
    )

    provider = SupabaseFileStorage(
        client=client,
        bucket=bucket,
    )

    service = FileStorageService(
        storage=provider,
    )

    return FileStorage(
        service=service,
    )