import logging
from time import perf_counter
from uuid import UUID

from module.ingest.knowledge.composition import (
    KnowledgeDiscoveryRequest,
    KnowledgeDiscoveryRequestItem,
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
            "[LR_NAVIGATION] start knowledge_space_id=%s intent=%s knowledge_request_count=%s",
            knowledge_space_id,
            analysis.intent,
            len(analysis.knowledge_requests),
        )

        step_started_at = perf_counter()
        logger.info("[LR_NAVIGATION] discovery_start")
        discovery = await self._knowledge_reader.discover(
            KnowledgeDiscoveryRequest(
                knowledge_space_id=knowledge_space_id,
                items=[
                    KnowledgeDiscoveryRequestItem(
                        request_id=f"knowledge_{index + 1}",
                        need=request.need,
                        document_type_seeds=(
                            request.document_type_seeds
                        ),
                        head_seeds=request.head_seeds,
                        topic_seeds=request.topic_seeds,
                        object_seeds=request.object_seeds,
                        identifier_seeds=request.identifier_seeds,
                        information_type_seeds=(
                            request.information_type_seeds
                        ),
                        information_field_seeds=(
                            request.information_field_seeds
                        ),
                        constraints=request.constraints,
                    )
                    for index, request in enumerate(
                        analysis.knowledge_requests
                    )
                ],
            )
        )
        logger.info(
            "[LR_NAVIGATION] discovery_done elapsed_ms=%s discovered_request_count=%s",
            int((perf_counter() - step_started_at) * 1000),
            len(discovery.requests),
        )

        if not discovery.requests:
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
            knowledge_candidates=discovery.requests,
        )
        logger.info(
            "[LR_NAVIGATION] selection_done elapsed_ms=%s selection_count=%s",
            int((perf_counter() - step_started_at) * 1000),
            len(selection_result.selections),
        )

        discovered_by_id = {
            request.request_id: request
            for request in discovery.requests
        }

        for selection in selection_result.selections:
            discovered_request = discovered_by_id.get(
                selection.request_id,
            )
            if discovered_request is None:
                continue

            step_started_at = perf_counter()
            logger.info(
                "[LR_NAVIGATION] retrieval_start request_id=%s",
                selection.request_id,
            )
            result = await self._knowledge_reader.retrieve(
                KnowledgeRetrievalRequest(
                    knowledge_space_id=knowledge_space_id,
                    discovered_request=discovered_request,
                    selection=KnowledgeRetrievalSelection(
                        request_id=selection.request_id,
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
                "[LR_NAVIGATION] retrieval_done request_id=%s elapsed_ms=%s item_count=%s",
                selection.request_id,
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
