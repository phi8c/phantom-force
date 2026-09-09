from module.ingest.knowledge.composition import (
    KnowledgeReader,
)
from module.launch_on_railway.knowledge_selection.composition import (
    KnowledgeSelector,
)
from module.launch_on_railway.navigation.application.services.navigation_service import (
    NavigationService,
)


def create_navigation_service(
    knowledge_reader: KnowledgeReader,
    knowledge_selector: KnowledgeSelector,
) -> NavigationService:
    return NavigationService(
        knowledge_reader=knowledge_reader,
        knowledge_selector=knowledge_selector,
    )
