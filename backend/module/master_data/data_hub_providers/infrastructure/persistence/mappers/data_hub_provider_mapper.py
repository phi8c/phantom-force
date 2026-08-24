from module.master_data.data_hub_providers.domain.entities.data_hub_provider import (
    DataHubProvider,
)

from module.master_data.data_hub_providers  .infrastructure.persistence.models.data_hub_provider_model import (
    DataHubProviderModel,
)


class DataHubProviderMapper:

    @staticmethod
    def to_entity(
        model: DataHubProviderModel,
    ) -> DataHubProvider:

        return DataHubProvider(
            id=model.id,
            code=model.code,
            name=model.name,
            provider=model.provider,
            configuration_schema=(
                model.configuration_schema
            ),
            enabled=model.enabled,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    @staticmethod
    def to_model(
        entity: DataHubProvider,
    ) -> DataHubProviderModel:

        return DataHubProviderModel(
            id=entity.id,
            code=entity.code,
            name=entity.name,
            provider=entity.provider,
            configuration_schema=(
                entity.configuration_schema
            ),
            enabled=entity.enabled,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )