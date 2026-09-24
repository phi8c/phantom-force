from __future__ import annotations

import asyncio
import json
import time
from datetime import datetime
from typing import Any, Callable

import httpx

from ..domain.configuration import DropboxConfiguration
from ..domain.entities.client_models import DropboxEntry, DropboxListPage


class DropboxClientError(RuntimeError):
    """A safe, provider-specific error raised by the Dropbox HTTP transport."""


class DropboxHttpClient:
    OAUTH_URL = "https://api.dropboxapi.com/oauth2/token"
    API_BASE_URL = "https://api.dropboxapi.com/2"
    CONTENT_BASE_URL = "https://content.dropboxapi.com/2"
    TOKEN_EXPIRY_MARGIN_SECONDS = 60.0

    def __init__(
        self,
        configuration: DropboxConfiguration,
        *,
        http_client: httpx.AsyncClient | None = None,
        timeout: float = 30.0,
        download_timeout: float = 60.0,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._configuration = configuration
        self._client = http_client or httpx.AsyncClient(timeout=timeout)
        self._owns_client = http_client is None
        self._request_timeout = timeout
        self._download_timeout = download_timeout
        self._clock = clock
        self._access_token: str | None = None
        self._access_token_expires_at = 0.0
        self._token_lock = asyncio.Lock()

    async def list_folder(self, path: str, *, recursive: bool) -> DropboxListPage:
        response = await self._authorized_post(
            f"{self.API_BASE_URL}/files/list_folder",
            json_body={"path": path, "recursive": recursive},
            resource=path or "/",
        )
        return self._to_page(self._response_json(response))

    async def list_folder_continue(self, cursor: str) -> DropboxListPage:
        response = await self._authorized_post(
            f"{self.API_BASE_URL}/files/list_folder/continue",
            json_body={"cursor": cursor},
            resource="list_folder cursor",
        )
        return self._to_page(self._response_json(response))

    async def download(self, identity: str) -> bytes:
        response = await self._authorized_post(
            f"{self.CONTENT_BASE_URL}/files/download",
            headers={
                "Dropbox-API-Arg": json.dumps(
                    {"path": identity}, separators=(",", ":")
                )
            },
            resource=identity,
            timeout=self._download_timeout,
        )
        return bytes(response.content)

    async def close(self) -> None:
        if self._owns_client:
            await self._client.aclose()

    async def __aenter__(self) -> DropboxHttpClient:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: Any,
    ) -> None:
        await self.close()

    async def _get_access_token(self) -> str:
        if self._token_is_valid():
            return str(self._access_token)

        async with self._token_lock:
            if self._token_is_valid():
                return str(self._access_token)
            await self._refresh_access_token()
            return str(self._access_token)

    def _token_is_valid(self) -> bool:
        return bool(
            self._access_token
            and self._clock() < self._access_token_expires_at
        )

    async def _refresh_access_token(self) -> None:
        try:
            response = await self._client.post(
                self.OAUTH_URL,
                data={
                    "grant_type": "refresh_token",
                    "refresh_token": self._configuration.refresh_token,
                },
                auth=httpx.BasicAuth(
                    self._configuration.app_key,
                    self._configuration.app_secret,
                ),
                timeout=self._request_timeout,
            )
        except httpx.TimeoutException as exc:
            raise DropboxClientError("Dropbox authentication request timed out.") from exc
        except httpx.RequestError as exc:
            raise DropboxClientError("Dropbox authentication request failed.") from exc

        if not response.is_success:
            raise DropboxClientError(
                f"Dropbox authentication failed (HTTP {response.status_code})."
            )

        payload = self._response_json(response, authentication=True)
        access_token = payload.get("access_token")
        expires_in = payload.get("expires_in")
        if not isinstance(access_token, str) or not access_token:
            raise DropboxClientError("Dropbox authentication response has no access token.")
        if not isinstance(expires_in, (int, float)) or expires_in <= 0:
            raise DropboxClientError("Dropbox authentication response has invalid expiry.")

        usable_lifetime = max(
            0.0,
            float(expires_in) - self.TOKEN_EXPIRY_MARGIN_SECONDS,
        )
        self._access_token = access_token
        self._access_token_expires_at = self._clock() + usable_lifetime

    async def _authorized_post(
        self,
        url: str,
        *,
        json_body: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        resource: str,
        timeout: float | None = None,
    ) -> httpx.Response:
        for attempt in range(2):
            token = await self._get_access_token()
            request_headers = dict(headers or {})
            request_headers["Authorization"] = f"Bearer {token}"
            try:
                response = await self._client.post(
                    url,
                    json=json_body,
                    headers=request_headers,
                    timeout=timeout or self._request_timeout,
                )
            except httpx.TimeoutException as exc:
                raise DropboxClientError("Dropbox request timed out.") from exc
            except httpx.RequestError as exc:
                raise DropboxClientError("Dropbox network request failed.") from exc

            if response.status_code == 401 and attempt == 0:
                self._access_token = None
                self._access_token_expires_at = 0.0
                continue
            if response.is_success:
                return response
            self._raise_api_error(response, resource)

        raise DropboxClientError("Dropbox authentication failed after token refresh.")

    @classmethod
    def _raise_api_error(cls, response: httpx.Response, resource: str) -> None:
        detail = cls._safe_error_detail(response)
        suffix = f": {detail}" if detail else ""
        if response.status_code == 401:
            raise DropboxClientError("Dropbox authentication failed (HTTP 401).")
        if response.status_code == 409 and "not_found" in detail.lower():
            raise DropboxClientError(f"Dropbox path not found: {resource}")
        if response.status_code == 429:
            retry_after = response.headers.get("Retry-After")
            retry_detail = (
                f" Retry after {retry_after} seconds." if retry_after else ""
            )
            raise DropboxClientError(
                f"Dropbox rate limit exceeded.{retry_detail}"
            )
        raise DropboxClientError(
            f"Dropbox API request failed (HTTP {response.status_code}){suffix}"
        )

    @staticmethod
    def _safe_error_detail(response: httpx.Response) -> str:
        try:
            payload = response.json()
        except ValueError:
            return ""
        if not isinstance(payload, dict):
            return ""
        value = payload.get("error_summary") or payload.get("error_description")
        return str(value)[:500] if value else ""

    @staticmethod
    def _response_json(
        response: httpx.Response,
        *,
        authentication: bool = False,
    ) -> dict[str, Any]:
        try:
            payload = response.json()
        except ValueError as exc:
            context = "authentication" if authentication else "API"
            raise DropboxClientError(
                f"Dropbox {context} returned invalid JSON."
            ) from exc
        if not isinstance(payload, dict):
            raise DropboxClientError("Dropbox API returned an invalid response shape.")
        return payload

    @classmethod
    def _to_page(cls, payload: dict[str, Any]) -> DropboxListPage:
        entries = payload.get("entries")
        if not isinstance(entries, list):
            raise DropboxClientError("Dropbox list response has no entries array.")
        return DropboxListPage(
            entries=[
                cls._to_entry(entry)
                for entry in entries
                if isinstance(entry, dict)
            ],
            cursor=(
                payload.get("cursor")
                if isinstance(payload.get("cursor"), str)
                else None
            ),
            has_more=bool(payload.get("has_more", False)),
        )

    @classmethod
    def _to_entry(cls, entry: dict[str, Any]) -> DropboxEntry:
        tag = entry.get(".tag")
        kind = tag if tag in {"file", "folder", "deleted"} else "deleted"
        return DropboxEntry(
            kind=kind,
            id=str(entry.get("id", "")),
            name=str(entry.get("name", "")),
            path_lower=cls._optional_string(entry.get("path_lower")),
            path_display=cls._optional_string(entry.get("path_display")),
            size=entry.get("size") if isinstance(entry.get("size"), int) else None,
            client_modified=cls._parse_datetime(entry.get("client_modified")),
            server_modified=cls._parse_datetime(entry.get("server_modified")),
            rev=cls._optional_string(entry.get("rev")),
            content_hash=cls._optional_string(entry.get("content_hash")),
        )

    @staticmethod
    def _optional_string(value: Any) -> str | None:
        return value if isinstance(value, str) else None

    @staticmethod
    def _parse_datetime(value: Any) -> datetime | None:
        if not isinstance(value, str) or not value:
            return None
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
