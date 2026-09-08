from enum import Enum


class QueryAnalysisPromptCode(Enum):
    ANALYZE_QUERY = "launch_on_railway.query_analysis"


class QueryAnalysisProviderCode(Enum):
    AZURE_OPENAI = "azure_openai"


class QueryAnalysisModelCode(Enum):
    ANALYZE_QUERY = "gpt-5.1"