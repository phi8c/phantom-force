from abc import ABC
from abc import abstractmethod


class PipelineStage(
    ABC,
):

    @abstractmethod
    async def execute(
        self,
        payload,
    ):
        pass