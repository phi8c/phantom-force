from module.launch_on_railway.query_analysis.composition import (
    QueryAnalysisResult,
)

from module.launch_on_railway.navigation.application.dtos.response.navigation_result import (
    NavigationResult,
)


class NavigationService:

    def __init__(
        self,
        knowledge_reader,
    ):
        self._knowledge_reader = knowledge_reader

    async def navigate(
        self,
        analysis: QueryAnalysisResult,
    ) -> NavigationResult:

        items = []

        for seed in analysis.seeds:
            matched_items = await self._knowledge_reader.search(
                object_code=seed.object_code,
                identifier_code=seed.identifier_code,
                information_type_code=seed.information_type_code,
                topic_codes=seed.topic_codes,
                constraints=seed.constraints,
            )

            items.extend(matched_items)

        return NavigationResult(
            items=items,
        )