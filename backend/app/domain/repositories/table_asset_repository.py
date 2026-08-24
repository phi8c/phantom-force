from abc import ABC
from abc import abstractmethod

from app.domain.entities.table_asset import (
    TableAsset,
)


class TableAssetRepository(
    ABC,
):

    @abstractmethod
    async def add(
        self,
        asset: TableAsset,
    ) -> TableAsset:
        pass