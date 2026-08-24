from abc import ABC
from abc import abstractmethod


class DocumentSource(ABC):

   
    @abstractmethod
    async def discover_files(
        self,
        run,
    ):
        pass

    @abstractmethod
    async def download_file(
        self,
        provider_metadata: dict,
    ) -> bytes:
        pass