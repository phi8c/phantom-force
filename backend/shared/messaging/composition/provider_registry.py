from __future__ import annotations

from collections.abc import Mapping

from .models import IngestDispatchers


class UnsupportedQueueProviderError(LookupError):
    pass


class MessagingProviderRegistry:
    def __init__(
        self,
        providers: Mapping[str, IngestDispatchers],
    ) -> None:
        normalized: dict[str, IngestDispatchers] = {}
        for code, dispatchers in providers.items():
            normalized_code = self.normalize_code(code)
            if normalized_code in normalized:
                raise ValueError(
                    f"Duplicate messaging provider code '{normalized_code}'."
                )
            normalized[normalized_code] = dispatchers
        if not normalized:
            raise ValueError("At least one messaging provider is required.")
        self._providers = normalized

    def get(self, provider_code: str) -> IngestDispatchers:
        normalized_code = self.normalize_code(provider_code)
        try:
            return self._providers[normalized_code]
        except KeyError as exc:
            raise UnsupportedQueueProviderError(
                f"Unsupported queue provider '{normalized_code}'."
            ) from exc

    @staticmethod
    def normalize_code(provider_code: str) -> str:
        normalized = provider_code.strip().lower()
        if not normalized:
            raise ValueError("Queue provider code must not be empty.")
        return normalized
