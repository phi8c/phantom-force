from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable, Mapping
from typing import Protocol

from .models import IngestDispatchers, IngestProducer


class UnsupportedQueueProviderError(LookupError):
    pass


class DispatcherProviderRegistry(Protocol):
    async def get(self, provider_code: str) -> IngestDispatchers:
        ...


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

    async def get(self, provider_code: str) -> IngestDispatchers:
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


ProducerFactory = Callable[[], Awaitable[IngestProducer]]


class LazyMessagingProviderRegistry:
    def __init__(self, factories: Mapping[str, ProducerFactory]) -> None:
        normalized: dict[str, ProducerFactory] = {}
        for code, factory in factories.items():
            normalized_code = MessagingProviderRegistry.normalize_code(code)
            if normalized_code in normalized:
                raise ValueError(
                    f"Duplicate messaging provider code '{normalized_code}'."
                )
            normalized[normalized_code] = factory
        if not normalized:
            raise ValueError("At least one messaging provider is required.")

        self._factories = normalized
        self._providers: dict[str, IngestProducer] = {}
        self._locks = {code: asyncio.Lock() for code in normalized}
        self._state_lock = asyncio.Lock()
        self._closed = False

    async def get(self, provider_code: str) -> IngestDispatchers:
        code = MessagingProviderRegistry.normalize_code(provider_code)
        try:
            factory = self._factories[code]
        except KeyError as exc:
            raise UnsupportedQueueProviderError(
                f"Unsupported queue provider '{code}'."
            ) from exc

        provider = self._providers.get(code)
        if provider is not None:
            return provider.dispatchers

        async with self._locks[code]:
            provider = self._providers.get(code)
            if provider is not None:
                return provider.dispatchers
            async with self._state_lock:
                if self._closed:
                    raise RuntimeError("Messaging provider registry is closed.")

            provider = await factory()
            async with self._state_lock:
                if self._closed:
                    await provider.close()
                    raise RuntimeError("Messaging provider registry is closed.")
                self._providers[code] = provider
            return provider.dispatchers

    async def close(self) -> None:
        async with self._state_lock:
            if self._closed:
                return
            self._closed = True
            providers = list(reversed(self._providers.values()))
            self._providers.clear()

        first_error: Exception | None = None
        for provider in providers:
            try:
                await provider.close()
            except Exception as exc:
                if first_error is None:
                    first_error = exc
        if first_error is not None:
            raise first_error
