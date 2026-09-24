from __future__ import annotations

from fastapi import FastAPI

from ...provider import DropboxProvider
from .router import get_dropbox_provider, router


def create_dropbox_http_app(provider: DropboxProvider) -> FastAPI:
    """Build an isolated app for Bruno/manual testing without production wiring."""
    app = FastAPI(title="Dropbox Data Hub Prototype")
    app.include_router(router)
    app.dependency_overrides[get_dropbox_provider] = lambda: provider
    return app
