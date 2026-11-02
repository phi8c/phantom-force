from dataclasses import dataclass
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from module.ingest.master.domain.contracts.master_config_lookup import MasterConfigLookup
from module.ingest.master.infrastructure.queries.master_config_lookup import SqlMasterConfigLookup


@dataclass(frozen=True)
class IngestionMasterConfig:
    extraction_engine_id: UUID
    chunking_strategy_id: UUID
    model_set_id: UUID | None


class IngestionMasterConfigResolver:

    def __init__(self, session: AsyncSession, lookup: MasterConfigLookup | None = None):
        self._lookup = lookup or SqlMasterConfigLookup(session)

    async def resolve(self, *, extraction_engine_code: str, chunking_strategy_code: str,
                      model_set_code: str | None = None) -> IngestionMasterConfig:
        extraction, chunking, model_set = await self._lookup.lookup(
            self._normalize_code(extraction_engine_code),
            self._normalize_code(chunking_strategy_code),
            self._normalize_code(model_set_code) if model_set_code else None,
        )
        if extraction is None:
            raise ValueError('extraction_engine_code is not available or disabled')
        if chunking is None:
            raise ValueError('chunking_strategy_code is not available or disabled')
        if model_set_code and model_set is None:
            raise ValueError('model_set_code is not available or disabled')
        return IngestionMasterConfig(extraction, chunking, model_set)

    @staticmethod
    def _normalize_code(
        code: str,
    ) -> str:

        normalized = code.strip().upper()

        if not normalized:
            raise ValueError(
                "code must not be empty"
            )

        return normalized
