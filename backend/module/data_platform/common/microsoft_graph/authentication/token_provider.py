from abc import ABC
from abc import abstractmethod


class TokenProvider(ABC):

    @abstractmethod
    async def get_token(self) -> str:
        ...