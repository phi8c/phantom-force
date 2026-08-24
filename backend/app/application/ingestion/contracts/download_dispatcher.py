from abc import ABC
from abc import abstractmethod
from uuid import UUID


class DownloadDispatcher(
    ABC,
):

    @abstractmethod
    async def dispatch(
        self,
        document_id: UUID,
    ):
        pass