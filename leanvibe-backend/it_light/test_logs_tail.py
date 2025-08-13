import os, sys, pytest
sys.path.insert(0, os.path.abspath("leanvibe-backend"))
os.environ.setdefault("LEANVIBE_DATABASE_URL", "sqlite+aiosqlite:///./leanvibe_test.db")
os.environ.setdefault("LEANVIBE_SECRET_KEY", "test_secret_key")

from uuid import uuid4
from datetime import datetime, timedelta

from app.api.endpoints.pipelines import tail_pipeline_logs
from app.services.mvp_service import mvp_service

pytestmark = pytest.mark.asyncio


class DummyCred:
    credentials = "token"


class DummyAuth:
    async def verify_token(self, token):
        return {"user_id": "u"}


class DummyTenant:
    def __init__(self, id):
        self.id = id


async def test_tail_once_filters(monkeypatch):
    # Seed in-memory logs for a mocked project
    project_id = uuid4()
    tenant_id = uuid4()
    # Insert fake project into in-memory store
    from app.models.mvp_models import MVPProject, MVPStatus, FounderInterview
    proj = MVPProject(
        id=project_id,
        tenant_id=tenant_id,
        project_name="T",
        slug="t",
        description="",
        status=MVPStatus.GENERATING,
        interview=FounderInterview(
            business_idea="a",
            target_market="b",
            value_proposition="c",
            problem_statement="p",
            target_audience="devs",
            core_features=["f1"],
        ),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    mvp_service._projects_storage[project_id] = proj

    # Seed logs
    now = datetime.utcnow()
    mvp_service._generation_logs[project_id] = [
        {"timestamp": now - timedelta(seconds=3), "level": "INFO", "message": "alpha", "stage": "backend"},
        {"timestamp": now - timedelta(seconds=2), "level": "ERROR", "message": "bravo", "stage": "frontend"},
        {"timestamp": now - timedelta(seconds=1), "level": "INFO", "message": "alpha two", "stage": "frontend"},
    ]

    import app.api.endpoints.pipelines as mod
    monkeypatch.setattr(mod, "auth_service", DummyAuth())

    # Run once mode, filter INFO and search 'alpha'
    resp = await tail_pipeline_logs(
        pipeline_id=project_id,
        credentials=DummyCred(),
        tenant=DummyTenant(tenant_id),
        level_filter="INFO",
        stage_filter=None,
        search="alpha",
        once=True,
    )
    # Collect body
    chunks = []
    async for c in resp.body_iterator:  # type: ignore[attr-defined]
        chunks.append(c)
    body = b"".join(chunks).decode()
    assert "alpha two" in body and "bravo" not in body
