from uuid import UUID

from module.ai.llm.application.dtos.ai_model_dto import (
    AIModelDTO,
)
from module.ai.llm.application.use_cases.models.create_ai_model import (
    CreateAIModelUseCase,
)
from module.ai.llm.application.use_cases.models.delete_ai_model import (
    DeleteAIModelUseCase,
)
from module.ai.llm.application.use_cases.models.get_ai_model import (
    GetAIModelUseCase,
)
from module.ai.llm.application.use_cases.models.get_ai_model_by_ref import (
    GetAIModelByRefUseCase,
)
from module.ai.llm.application.use_cases.models.list_ai_models import (
    ListAIModelsUseCase,
)
from module.ai.llm.application.use_cases.models.update_ai_model import (
    UpdateAIModelUseCase,
)


class AIModelAdminService:

    def __init__(
        self,
        create_model: CreateAIModelUseCase,
        get_model: GetAIModelUseCase,
        get_model_by_ref: GetAIModelByRefUseCase,
        list_models: ListAIModelsUseCase,
        update_model: UpdateAIModelUseCase,
        delete_model: DeleteAIModelUseCase,
    ):
        self._create_model = create_model
        self._get_model = get_model
        self._get_model_by_ref = get_model_by_ref
        self._list_models = list_models
        self._update_model = update_model
        self._delete_model = delete_model

    async def create(
        self,
        model: AIModelDTO,
    ) -> AIModelDTO:

        return await self._create_model.execute(
            model,
        )

    async def get_by_id(
        self,
        model_id: UUID,
    ) -> AIModelDTO | None:

        return await self._get_model.execute(
            model_id,
        )

    async def get(
        self,
        provider_code: str,
        model_code: str,
    ) -> AIModelDTO | None:

        return await self._get_model_by_ref.execute(
            provider_code=provider_code,
            model_code=model_code,
        )

    async def list(
        self,
    ) -> list[AIModelDTO]:

        return await self._list_models.execute()

    async def update(
        self,
        model: AIModelDTO,
    ) -> AIModelDTO:

        return await self._update_model.execute(
            model,
        )

    async def delete(
        self,
        model_id: UUID,
    ) -> None:

        await self._delete_model.execute(
            model_id,
        )
