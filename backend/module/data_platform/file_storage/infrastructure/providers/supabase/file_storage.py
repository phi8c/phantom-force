from supabase import Client

from module.data_platform.file_storage.domain.contracts.file_storage import (
    FileStorage,
)


class SupabaseFileStorage(
    FileStorage,
):

    def __init__(
        self,
        client: Client,
        bucket: str,
    ) -> None:
        self._client = client
        self._bucket = bucket

    async def upload(
        self,
        path: str,
        content: bytes,
        content_type: str | None = None,
    ) -> str:

        file_options: dict[str, str] = {
            "upsert": "true",
        }

        if content_type:
            file_options["content-type"] = content_type

        (
            self._client.storage
            .from_(self._bucket)
            .upload(
                path=path,
                file=content,
                file_options=file_options,
            )
        )

        return path

    async def download(
        self,
        path: str,
    ) -> bytes:

        return (
            self._client.storage
            .from_(self._bucket)
            .download(
                path,
            )
        )

    async def delete(
        self,
        path: str,
    ) -> None:

        (
            self._client.storage
            .from_(self._bucket)
            .remove(
                [path],
            )
        )