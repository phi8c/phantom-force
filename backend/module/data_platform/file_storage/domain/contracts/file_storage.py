from abc import ABC
from abc import abstractmethod


class FileStorage(ABC):

    @abstractmethod
    async def upload(
        self,
        path: str,
        content: bytes,
        content_type: str | None = None,
    ) -> str:
        ...

    @abstractmethod
    async def download(
        self,
        path: str,
    ) -> bytes:
        ...

    @abstractmethod
    async def delete(
        self,
        path: str,
    ) -> None:
        ...