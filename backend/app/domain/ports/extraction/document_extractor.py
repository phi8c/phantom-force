from abc import ABC
from abc import abstractmethod


class DocumentExtractor(
    ABC,
):

    @abstractmethod
    async def extract(
        self,
        file_path: str,
    ) -> tuple[str, int]:
        pass