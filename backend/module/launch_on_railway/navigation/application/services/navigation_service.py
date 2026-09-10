import logging
from time import perf_counter
from uuid import UUID

from module.ingest.knowledge.composition import (
    KnowledgeDiscoveryRequest,
    KnowledgeDiscoverySeed,
    KnowledgeReader,
    KnowledgeRetrievalRequest,
    KnowledgeRetrievalSelection,
)
from module.launch_on_railway.knowledge_selection.composition import (
    KnowledgeSelector,
)
from module.launch_on_railway.query_analysis.composition import (
    QueryAnalysisResult,
)

from module.launch_on_railway.navigation.application.dtos.response.navigation_result import (
    NavigationItem,
    NavigationResult,
)


logger = logging.getLogger(__name__)


class NavigationService:

    def __init__(
        self,
        knowledge_reader: KnowledgeReader,
        knowledge_selector: KnowledgeSelector,
    ):
        self._knowledge_reader = knowledge_reader
        self._knowledge_selector = knowledge_selector

    async def navigate(
        self,
        *,
        knowledge_space_id: UUID,
        question: str,
        analysis: QueryAnalysisResult,
    ) -> NavigationResult:

        items: list[NavigationItem] = []
        seen_information_ids: set[str] = set()
        started_at = perf_counter()

        logger.info(
            "[LR_NAVIGATION] start knowledge_space_id=%s intent=%s seed_count=%s",
            knowledge_space_id,
            analysis.intent,
            len(analysis.seeds),
        )

        step_started_at = perf_counter()
        logger.info("[LR_NAVIGATION] discovery_start")
        discovery = await self._knowledge_reader.discover(
            KnowledgeDiscoveryRequest(
                knowledge_space_id=knowledge_space_id,
                seeds=[
                    KnowledgeDiscoverySeed(
                        seed_id=f"seed_{index + 1}",
                        object_code=seed.object_code,
                        identifier_code=seed.identifier_code,
                        information_type_code=(
                            seed.information_type_code
                        ),
                        topic_codes=seed.topic_codes,
                        constraints=seed.constraints,
                    )
                    for index, seed in enumerate(analysis.seeds)
                ],
            )
        )
        logger.info(
            "[LR_NAVIGATION] discovery_done elapsed_ms=%s discovered_seed_count=%s",
            int((perf_counter() - step_started_at) * 1000),
            len(discovery.seeds),
        )

        if not discovery.seeds:
            logger.info(
                "[LR_NAVIGATION] completed total_information=%s elapsed_ms=%s",
                len(items),
                int((perf_counter() - started_at) * 1000),
            )
            return NavigationResult(
                items=items,
            )

        step_started_at = perf_counter()
        logger.info("[LR_NAVIGATION] selection_start")
        selection_result = await self._knowledge_selector.select(
            question=question,
            candidate_seeds=discovery.seeds,
        )
        logger.info(
            "[LR_NAVIGATION] selection_done elapsed_ms=%s selection_count=%s",
            int((perf_counter() - step_started_at) * 1000),
            len(selection_result.selections),
        )

        discovered_by_id = {
            seed.seed_id: seed
            for seed in discovery.seeds
        }

        for selection in selection_result.selections:
            discovered_seed = discovered_by_id.get(
                selection.seed_id,
            )
            if discovered_seed is None:
                continue

            step_started_at = perf_counter()
            logger.info(
                "[LR_NAVIGATION] retrieval_start seed_id=%s",
                selection.seed_id,
            )
            result = await self._knowledge_reader.retrieve(
                KnowledgeRetrievalRequest(
                    knowledge_space_id=knowledge_space_id,
                    discovered_seed=discovered_seed,
                    selection=KnowledgeRetrievalSelection(
                        seed_id=selection.seed_id,
                        information_type_codes=(
                            selection.information_type_codes
                        ),
                        topic_codes=selection.topic_codes,
                        field_codes=selection.field_codes,
                        constraints=selection.constraints,
                    ),
                )
            )
            logger.info(
                "[LR_NAVIGATION] retrieval_done seed_id=%s elapsed_ms=%s item_count=%s",
                selection.seed_id,
                int((perf_counter() - step_started_at) * 1000),
                len(result.items),
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
                        information_type_code=(
                            item.information_type_code
                        ),
                        data=item.data,
                        object_refs=item.object_refs,
                        topic_refs=item.topic_refs,
                        source_refs=item.source_refs,
                        confidence=item.confidence,
                    )
                )

        logger.info(
            "[LR_NAVIGATION] completed total_information=%s elapsed_ms=%s",
            len(items),
            int((perf_counter() - started_at) * 1000),
        )

        return NavigationResult(
            items=items,
        )
