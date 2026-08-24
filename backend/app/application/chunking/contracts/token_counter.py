from abc import ABC
from abc import abstractmethod


class TokenCounter(
    ABC,
):

    @abstractmethod
    def count(
        self,
        text: str,
    ) -> int:
        pass