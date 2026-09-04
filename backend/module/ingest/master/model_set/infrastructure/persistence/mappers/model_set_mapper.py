from module.ingest.master.model_set.domain.entities.model_set import (
    ModelSet,
)
from module.ingest.master.model_set.infrastructure.persistence.models.model_set_model import (
    ModelSetModel,
)


class ModelSetMapper:

    @staticmethod
    def to_entity(
        model: ModelSetModel,
    ) -> ModelSet:

        return ModelSet(
            id=model.id,
            feature_id=model.feature_id,
            code=model.code,
            name=model.name,
            description=model.description,
            enabled=model.enabled,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    @staticmethod
    def to_model(
        entity: ModelSet,
    ) -> ModelSetModel:

        return ModelSetModel(
            id=entity.id,
            feature_id=entity.feature_id,
            code=entity.code,
            name=entity.name,
            description=entity.description,
            enabled=entity.enabled,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )
