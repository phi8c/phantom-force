from pydantic import BaseModel
from uuid import UUID


class GraphConfiguration(
    BaseModel,
):
    enabled: bool = False


class ChunkConfiguration(
    BaseModel,
):
    mode: str 

    level: int | None = 1

    max_chunk_tokens: int 


class TableConfiguration(
    BaseModel,
):
    storage_provider: str 
       

class IngestionConfiguration(
    BaseModel,
):
    graph: GraphConfiguration

    chunk: ChunkConfiguration

    table: TableConfiguration


class StartIngestionRequest(
    BaseModel,
):
    source_id: UUID
    
    trigger_type: str

    scope_type: str

    site_id: str | None = None

    drive_id: str | None = None

    folder_id: str | None = None

    file_id: str | None = None

    configuration: (
        IngestionConfiguration
    )