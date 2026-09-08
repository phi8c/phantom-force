from uuid import UUID

from module.ingest.knowledge.composition import (
    KnowledgeReader,
    KnowledgeSearchRequest,
)
from module.launch_on_railway.query_analysis.composition import (
    QueryAnalysisResult,
)

from module.launch_on_railway.navigation.application.dtos.response.navigation_result import (
    NavigationItem,
    NavigationResult,
)


class NavigationService:

    def __init__(
        self,
        knowledge_reader: KnowledgeReader,
    ):
        self._knowledge_reader = knowledge_reader

    async def navigate(
        self,
        *,
        knowledge_space_id: UUID,
        analysis: QueryAnalysisResult,
    ) -> NavigationResult:

        items: list[NavigationItem] = []
        seen_information_ids: set[str] = set()

        for seed in analysis.seeds:
            result = await self._knowledge_reader.search_information(
                KnowledgeSearchRequest(
                    knowledge_space_id=knowledge_space_id,
                    object_code=seed.object_code,
                    identifier_code=seed.identifier_code,
                    information_type_code=(
                        seed.information_type_code
                    ),
                    topic_codes=seed.topic_codes,
                    constraints=seed.constraints,
                )
            )

            for item in result.items:
                information_id = str(item.information_id)
                if information_id in seen_information_ids:
                    continue

                seen_information_ids.add(information_id)
                items.append(
                    NavigationItem(
                        information_id=information_id,
                        summary=item.summary,
                        data=item.data,
                        source_refs=item.source_refs,
                        confidence=item.confidence,
                    )
                )

        return NavigationResult(
            items=items,
        )
