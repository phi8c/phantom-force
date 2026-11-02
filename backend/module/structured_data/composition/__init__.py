"""Public structured-data boundary; infrastructure is assembled only here."""
from module.structured_data.domain.models import QueryResult
from module.structured_data.application.services import StructuredBuildService, StructuredQueryService
from module.structured_data.application.query_compiler import QueryRejected


def create_structured_builder(*, session, object_storage):
    from module.ingest.config.composition import create_ingestion_config_service
    from module.ingest.embedding.composition import create_text_embedding_provider
    from module.structured_data.infrastructure.artifacts import FileStorageArtifacts
    from module.structured_data.infrastructure.catalog import SqlDatasetCatalog
    from module.structured_data.infrastructure.workbook import XlsxWorkbookBuilder
    return StructuredBuildService(builder=XlsxWorkbookBuilder(), catalog=SqlDatasetCatalog(session),
        artifacts=FileStorageArtifacts(uploader=object_storage),config_service=create_ingestion_config_service(session),
        embedder_factory=lambda space: create_text_embedding_provider(session=session,knowledge_space_id=space))


def create_structured_reader(*, session, file_storage, gateway, prompt_provider):
    import os
    from pathlib import Path
    from module.ingest.embedding.composition import create_text_embedding_provider
    from module.structured_data.infrastructure.artifacts import FileStorageArtifacts
    from module.structured_data.infrastructure.catalog import SqlDatasetCatalog
    from module.structured_data.infrastructure.planner import LLMStructuredPlanner
    from module.structured_data.infrastructure.query_engine import DuckDbQueryEngine
    from module.structured_data.infrastructure.cache import CachedArtifacts
    cache = Path(os.environ.get('STRUCTURED_DATA_CACHE_DIR', str(Path(__file__).resolve().parents[3]/'temp'/'structured-query-cache')))
    return StructuredQueryService(catalog=SqlDatasetCatalog(session),artifacts=CachedArtifacts(FileStorageArtifacts(file_storage),cache),
        planner=LLMStructuredPlanner(gateway=gateway,prompt_provider=prompt_provider),engine=DuckDbQueryEngine(),
        embedder_factory=lambda space: create_text_embedding_provider(session=session,knowledge_space_id=space))


__all__ = ['QueryResult','QueryRejected','StructuredBuildService','StructuredQueryService','create_structured_builder','create_structured_reader']
