from dataclasses import dataclass


@dataclass(frozen=True)
class QueryAnalysisRequest:
    question: str