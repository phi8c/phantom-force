from dataclasses import dataclass


@dataclass(frozen=True)
class AIModelRef:

    provider_code: str

    model_code: str
