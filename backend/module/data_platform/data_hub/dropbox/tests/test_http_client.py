from __future__ import annotations

import json
import unittest
from urllib.parse import parse_qs

import httpx

from module.data_platform.data_hub.dropbox.domain.configuration import (
    DropboxConfiguration,
)
from module.data_platform.data_hub.dropbox.infrastructure.client import (
    DropboxClientError,
    DropboxHttpClient,
)


def configuration() -> DropboxConfiguration:
    return DropboxConfiguration.from_mapping(
        {
            "app_key": "test-key",
            "app_secret": "test-secret",
            "refresh_token": "test-refresh",
            "root_path": "/RT_Test",
        }
    )


class DropboxHttpClientTests(unittest.IsolatedAsyncioTestCase):
    async def test_refreshes_token_once_and_reuses_cached_token(self) -> None:
        requests: list[httpx.Request] = []

        def handler(request: httpx.Request) -> httpx.Response:
            requests.append(request)
            if request.url == httpx.URL(DropboxHttpClient.OAUTH_URL):
                form = parse_qs(request.content.decode())
                self.assertEqual(form["grant_type"], ["refresh_token"])
                self.assertEqual(form["refresh_token"], ["test-refresh"])
                self.assertTrue(request.headers["Authorization"].startswith("Basic "))
                return httpx.Response(
                    200,
                    json={"access_token": "token-1", "expires_in": 14400},
                )
            self.assertEqual(request.headers["Authorization"], "Bearer token-1")
            return httpx.Response(
                200,
                json={"entries": [], "cursor": "cursor", "has_more": False},
            )

        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http:
            client = DropboxHttpClient(configuration(), http_client=http)
            await client.list_folder("/RT_Test", recursive=False)
            await client.list_folder("/RT_Test", recursive=True)

        oauth_requests = [
            request
            for request in requests
            if request.url == httpx.URL(DropboxHttpClient.OAUTH_URL)
        ]
        self.assertEqual(len(oauth_requests), 1)

    async def test_list_folder_uses_endpoint_and_normalizes_entries(self) -> None:
        seen_body: dict[str, object] = {}

        def handler(request: httpx.Request) -> httpx.Response:
            if request.url == httpx.URL(DropboxHttpClient.OAUTH_URL):
                return httpx.Response(
                    200,
                    json={"access_token": "token", "expires_in": 14400},
                )
            self.assertEqual(
                str(request.url),
                f"{DropboxHttpClient.API_BASE_URL}/files/list_folder",
            )
            seen_body.update(json.loads(request.content))
            return httpx.Response(
                200,
                json={
                    "entries": [
                        {
                            ".tag": "folder",
                            "id": "id:folder",
                            "name": "Docs",
                            "path_lower": "/rt_test/docs",
                            "path_display": "/RT_Test/Docs",
                        },
                        {
                            ".tag": "file",
                            "id": "id:file",
                            "name": "report.pdf",
                            "path_lower": "/rt_test/docs/report.pdf",
                            "path_display": "/RT_Test/Docs/report.pdf",
                            "size": 42,
                            "server_modified": "2026-01-02T03:04:05Z",
                            "rev": "rev-1",
                            "content_hash": "hash-1",
                        },
                    ],
                    "cursor": "next",
                    "has_more": True,
                },
            )

        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http:
            page = await DropboxHttpClient(
                configuration(), http_client=http
            ).list_folder("/RT_Test", recursive=True)

        self.assertEqual(seen_body, {"path": "/RT_Test", "recursive": True})
        self.assertEqual([entry.kind for entry in page.entries], ["folder", "file"])
        self.assertEqual(page.entries[1].size, 42)
        self.assertEqual(page.entries[1].server_modified.year, 2026)
        self.assertEqual(page.cursor, "next")
        self.assertTrue(page.has_more)

    async def test_list_folder_continue_sends_cursor(self) -> None:
        bodies: list[dict[str, object]] = []

        def handler(request: httpx.Request) -> httpx.Response:
            if request.url == httpx.URL(DropboxHttpClient.OAUTH_URL):
                return httpx.Response(
                    200,
                    json={"access_token": "token", "expires_in": 14400},
                )
            self.assertEqual(
                str(request.url),
                f"{DropboxHttpClient.API_BASE_URL}/files/list_folder/continue",
            )
            bodies.append(json.loads(request.content))
            return httpx.Response(
                200,
                json={"entries": [], "cursor": "next-2", "has_more": False},
            )

        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http:
            page = await DropboxHttpClient(
                configuration(), http_client=http
            ).list_folder_continue("next-1")

        self.assertEqual(bodies, [{"cursor": "next-1"}])
        self.assertEqual(page.cursor, "next-2")

    async def test_download_sends_api_argument_and_returns_bytes(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            if request.url == httpx.URL(DropboxHttpClient.OAUTH_URL):
                return httpx.Response(
                    200,
                    json={"access_token": "token", "expires_in": 14400},
                )
            self.assertEqual(
                str(request.url),
                f"{DropboxHttpClient.CONTENT_BASE_URL}/files/download",
            )
            self.assertEqual(
                json.loads(request.headers["Dropbox-API-Arg"]),
                {"path": "id:file"},
            )
            self.assertEqual(request.content, b"")
            return httpx.Response(200, content=b"file-content")

        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http:
            content = await DropboxHttpClient(
                configuration(), http_client=http
            ).download("id:file")

        self.assertEqual(content, b"file-content")

    async def test_oauth_failure_raises_safe_error(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(
                400,
                json={"error_description": "invalid refresh token"},
            )

        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http:
            client = DropboxHttpClient(configuration(), http_client=http)
            with self.assertRaisesRegex(
                DropboxClientError,
                r"Dropbox authentication failed \(HTTP 400\)",
            ):
                await client.list_folder("/RT_Test", recursive=False)

    async def test_api_error_maps_path_not_found(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            if request.url == httpx.URL(DropboxHttpClient.OAUTH_URL):
                return httpx.Response(
                    200,
                    json={"access_token": "token", "expires_in": 14400},
                )
            return httpx.Response(
                409,
                json={"error_summary": "path/not_found/"},
            )

        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http:
            client = DropboxHttpClient(configuration(), http_client=http)
            with self.assertRaisesRegex(
                DropboxClientError,
                "Dropbox path not found: /RT_Test/missing",
            ):
                await client.list_folder("/RT_Test/missing", recursive=False)

    async def test_unauthorized_refreshes_and_retries_once(self) -> None:
        oauth_calls = 0
        api_calls = 0

        def handler(request: httpx.Request) -> httpx.Response:
            nonlocal oauth_calls, api_calls
            if request.url == httpx.URL(DropboxHttpClient.OAUTH_URL):
                oauth_calls += 1
                return httpx.Response(
                    200,
                    json={
                        "access_token": f"token-{oauth_calls}",
                        "expires_in": 14400,
                    },
                )
            api_calls += 1
            if api_calls == 1:
                self.assertEqual(request.headers["Authorization"], "Bearer token-1")
                return httpx.Response(401, json={"error_summary": "expired_access_token/"})
            self.assertEqual(request.headers["Authorization"], "Bearer token-2")
            return httpx.Response(
                200,
                json={"entries": [], "cursor": "done", "has_more": False},
            )

        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http:
            page = await DropboxHttpClient(
                configuration(), http_client=http
            ).list_folder("/RT_Test", recursive=False)

        self.assertEqual(page.cursor, "done")
        self.assertEqual(oauth_calls, 2)
        self.assertEqual(api_calls, 2)

    async def test_timeout_raises_clear_error(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            if request.url == httpx.URL(DropboxHttpClient.OAUTH_URL):
                return httpx.Response(
                    200,
                    json={"access_token": "token", "expires_in": 14400},
                )
            raise httpx.ReadTimeout("timed out", request=request)

        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http:
            client = DropboxHttpClient(configuration(), http_client=http)
            with self.assertRaisesRegex(
                DropboxClientError,
                "Dropbox request timed out",
            ):
                await client.list_folder("/RT_Test", recursive=False)


if __name__ == "__main__":
    unittest.main()
