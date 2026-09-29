from dataclasses import dataclass


@dataclass(frozen=True)
class StartOidcResult:
    authorization_url: str
