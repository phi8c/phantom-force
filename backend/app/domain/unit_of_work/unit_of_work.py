from abc import ABC
from abc import abstractmethod


class UnitOfWork(ABC):

    @abstractmethod
    async def commit(self):
        pass

    @abstractmethod
    async def rollback(self):
        pass
    
    