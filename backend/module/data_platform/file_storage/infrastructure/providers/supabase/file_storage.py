from __future__ import annotations

import os
import tempfile
from collections.abc import AsyncIterator

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

    async def upload_stream(
        self,
        path: str,
        content: AsyncIterator[bytes],
        content_type: str | None = None,
    ) -> str:

        temp_path: str | None = None

        try:
            with tempfile.NamedTemporaryFile(
                mode="wb",
                delete=False,
            ) as temp_file:

                temp_path = temp_file.name

                async for chunk in content:
                    if chunk:
                        temp_file.write(chunk)

            file_options: dict[str, str] = {
                "upsert": "true",
            }

            if content_type:
                file_options[
                    "content-type"
                ] = content_type

            with open(
                temp_path,
                "rb",
            ) as file:

                (
                    self._client.storage
                    .from_(self._bucket)
                    .upload(
                        path=path,
                        file=file,
                        file_options=file_options,
                    )
                )

            return path

        finally:
            if (
                temp_path
                and os.path.exists(
                    temp_path
                )
            ):
                os.remove(
                    temp_path
                )

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