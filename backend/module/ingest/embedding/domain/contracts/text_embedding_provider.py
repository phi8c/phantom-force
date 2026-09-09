from abc import ABC
from abc import abstractmethod


class TextEmbeddingProvider(ABC):

    @abstractmethod
    async def embed_texts(
        self,
        texts: list[str],
    ) -> list[list[float]]:
        pass
