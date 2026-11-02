from sqlalchemy import func, literal, select

from module.ingest.master.extraction_strategy.infrastructure.persistence.models.extraction_strategy_model import ExtractionStrategyModel
from module.ingest.master.chunking_strategy.infrastructure.persistence.models.chunking_strategy_model import ChunkingStrategyModel
from module.ingest.master.model_set.infrastructure.persistence.models.model_set_model import ModelSetModel


class SqlMasterConfigLookup:
    """Resolve independent enabled IDs in one round trip on the same session."""

    def __init__(self, session):
        self.session = session

    async def lookup(self, extraction_code, chunking_code, model_set_code):
        def enabled_id(model, code):
            return select(model.id).where(func.upper(model.code) == code,
                                          model.enabled.is_(True)).scalar_subquery()
        statement = select(enabled_id(ExtractionStrategyModel, extraction_code),
                           enabled_id(ChunkingStrategyModel, chunking_code),
                           enabled_id(ModelSetModel, model_set_code) if model_set_code else literal(None))
        return tuple((await self.session.execute(statement)).one())
