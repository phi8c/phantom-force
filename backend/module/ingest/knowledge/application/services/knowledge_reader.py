from module.ingest.knowledge.application.dtos.knowledge_search_request import (
    KnowledgeSearchRequest,
)
from module.ingest.knowledge.application.dtos.knowledge_search_result import (
    KnowledgeSearchItem,
    KnowledgeSearchResult,
)
from module.ingest.knowledge.domain.contracts.knowledge_repository import (
    KnowledgeRepository,
)


class KnowledgeReader:

    def __init__(
        self,
        repository: KnowledgeRepository,
    ):
        self._repository = repository

    async def search_information(
        self,
        request: KnowledgeSearchRequest,
    ) -> KnowledgeSearchResult:

        records = await self._repository.search_information(
            knowledge_space_id=request.knowledge_space_id,
            object_code=request.object_code,
            identifier_code=request.identifier_code,
            information_type_code=request.information_type_code,
            topic_codes=request.topic_codes,
        )

        return KnowledgeSearchResult(
            items=[
                KnowledgeSearchItem(
                    information_id=record.information_id,
                    information_type_code=record.information_type_code,
                    summary=record.summary,
                    data=record.data,
                    object_refs=record.object_refs or [],
                    topic_refs=record.topic_refs or [],
                    source_refs=record.source_refs or [],
                    confidence=record.confidence,
                )
                for record in records
            ],
        )
