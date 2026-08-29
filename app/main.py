"""FastAPI entrypoint."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes import router
from app.db import get_engine
from app.logging_config import configure_logging
from app.services.ai_ops_service import AIOpsService
from app.settings import ensure_data_dir, get_settings


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    configure_logging(settings.log_level)
    ensure_data_dir()
    get_engine()
    if not getattr(app.state, "aiops", None):
        app.state.aiops = AIOpsService()
    yield
    service = getattr(app.state, "aiops", None)
    if service is not None:
        service.close()


app = FastAPI(
    title="Enterprise AI Operations Control Plane",
    description=("Reference architecture for operating AI as a governed enterprise capability."),
    version="0.1.0",
    lifespan=lifespan,
)
app.include_router(router)
