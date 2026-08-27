from integration.ingest.chunking.factory import (
    create_chunk_document_use_case_scope_with_downstream,
)
from integration.ingest.classification.factory import (
    create_classify_batch_use_case_scope,
)
from integration.ingest.discovery.factory import (
    create_discover_batch_use_case_scope,
)
from integration.ingest.download.factory import (
    create_download_file_use_case_scope,
)
from integration.ingest.embedding.factory import (
    create_embed_batch_use_case_scope,
)
from integration.ingest.extraction.factory import (
    create_extract_document_use_case_scope_with_chunking,
)

from bootstrap.database import async_session_factory


def download_use_case_scope(
    *,
    document_source,
    object_storage,
    extraction_dispatcher,
):

    return create_download_file_use_case_scope(
        session_factory=async_session_factory,
        document_source=document_source,
        object_storage=object_storage,
        extraction_dispatcher=extraction_dispatcher,
    )


def discovery_use_case_scope(
    *,
    data_hub_provider_resolver,
    download_dispatcher,
):

    return create_discover_batch_use_case_scope(
        session_factory=async_session_factory,
        data_hub_provider_resolver=(
            data_hub_provider_resolver
        ),
        download_dispatcher=download_dispatcher,
    )


def extraction_use_case_scope(
    *,
    file_storage,
    object_storage,
    chunking_dispatcher,
):

    return (
        create_extract_document_use_case_scope_with_chunking(
            session_factory=async_session_factory,
            file_storage=file_storage,
            object_storage=object_storage,
            chunking_dispatcher=chunking_dispatcher,
        )
    )


def chunking_use_case_scope(
    *,
    file_storage,
    embedding_dispatcher,
    classification_dispatcher,
):

    return (
        create_chunk_document_use_case_scope_with_downstream(
            session_factory=async_session_factory,
            file_storage=file_storage,
            embedding_dispatcher=embedding_dispatcher,
            classification_dispatcher=(
                classification_dispatcher
            ),
        )
    )


def embedding_use_case_scope():

    return create_embed_batch_use_case_scope(
        session_factory=async_session_factory,
    )


def classification_use_case_scope():

    return create_classify_batch_use_case_scope(
        session_factory=async_session_factory,
    )
