from module.ingest.knowledge.composition import (
    KnowledgeReader,
)
from module.launch_on_railway.navigation.application.services.navigation_service import (
    NavigationService,
)


def create_navigation_service(
    knowledge_reader: KnowledgeReader,
) -> NavigationService:
    return NavigationService(
        knowledge_reader=knowledge_reader,
    )
