import os, sys
sys.path.insert(0, os.path.abspath("leanvibe-backend"))
os.environ.setdefault("LEANVIBE_DATABASE_URL", "sqlite+aiosqlite:///./leanvibe_test.db")
os.environ.setdefault("LEANVIBE_SECRET_KEY", "test_secret_key")
import asyncio
from uuid import uuid4

import pytest
from app.services.mvp_service import mvp_service


class DummyAuth:
    async def verify_token(self, token: str):
        return {"sub": "test"}


@pytest.mark.asyncio
async def test_tail_once_with_token(monkeypatch):
    # Minimal env to satisfy settings
    os.environ.setdefault("LEANVIBE_SECRET_KEY", "test_secret_key")
    # Arrange: create a fake project and logs
    tenant_id = uuid4()
    project_id = uuid4()
    mvp_service._projects_storage[project_id] = type("M", (), {
        "id": project_id,
        "tenant_id": tenant_id,
        "status": type("S", (), {"value": "generating"})(),
    })()
    # Seed logs
    mvp_service._generation_logs[project_id] = [
        {"timestamp": None, "level": "INFO", "stage": "backend_development", "message": "hello"}
    ]

    import app.api.endpoints.pipelines as mod
    monkeypatch.setattr(mod, "auth_service", DummyAuth())

    from app.api.endpoints.pipelines import tail_pipeline_logs

    class DummyTenant:
        def __init__(self, id):
            self.id = id

    # Act: call endpoint function directly
    resp = await tail_pipeline_logs(
        pipeline_id=project_id,
        credentials=None,
        tenant=DummyTenant(tenant_id),
        level_filter=None,
        stage_filter=None,
        search=None,
        once=True,
        token="any",
    )
    chunks = []
    async for c in resp.body_iterator:  # type: ignore[attr-defined]
        chunks.append(c)
    body = b"".join(chunks)
    assert b"data:" in body
