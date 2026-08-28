from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str

    DATABASE_URL: str

    AZURE_SERVICE_BUS_CONNECTION_STRING: str | None = None
    
    
    SUPABASE_URL: str
    SUPABASE_KEY: str
    SUPABASE_STORAGE_BUCKET: str = "document"
    
    
    
    AZURE_SERVICE_BUS_QUEUE_NAME: str | None = None

    GRAPH_TENANT_ID: str | None = None
    GRAPH_CLIENT_ID: str | None = None
    GRAPH_CLIENT_SECRET: str | None = None
    
    GRAPH_BASE_URL: str
    GRAPH_SCOPE: str

    AZURE_SEARCH_ENDPOINT: str | None = None
    AZURE_SEARCH_API_KEY: str | None = None
    AZURE_SEARCH_INDEX_NAME: str | None = None
    SHAREPOINT_DRIVE_ID: str | None = None
    
    AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT: str
    
    
    AZURE_SERVICE_BUS_EVENT_TOPIC: str | None = None

    AZURE_DOCUMENT_INTELLIGENCE_KEY: str
    
    AZURE_SERVICE_BUS_EVENT_QUEUE: str | None = None
    
    AZURE_SERVICE_BUS_EXTRACT_QUEUE: str | None = None
    
    
    # settings.py

 

    
    
    AZURE_SERVICE_BUS_DOWNLOAD_QUEUE: str

    AZURE_SERVICE_BUS_EXTRACT_QUEUE: str

    AZURE_SERVICE_BUS_CHUNK_QUEUE: str

    AZURE_SERVICE_BUS_EMBED_QUEUE: str

    AZURE_SERVICE_BUS_CLASSIFY_QUEUE: str

    AZURE_SERVICE_BUS_INDEX_QUEUE: str
    
    AZURE_OPENAI_ENDPOINT: str
    AZURE_OPENAI_API_KEY: str
    AZURE_OPENAI_API_VERSION: str
    AZURE_OPENAI_EMBEDDING_DEPLOYMENT: str
    AZURE_ENPOINT_NAME: str
    
    
    
    class Config:
        env_file = (
            ".env",
            "backend/.env",
        )
        extra = "ignore"


settings = Settings()
