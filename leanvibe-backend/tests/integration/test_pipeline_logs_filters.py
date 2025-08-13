import os
os.environ.setdefault("LEANVIBE_DATABASE_URL", "sqlite+aiosqlite:///./leanvibe_test.db")
os.environ.setdefault("LEANVIBE_SECRET_KEY", "test_secret_key")

import pytest
import pytest_asyncio
import asyncio
from uuid import uuid4
from datetime import datetime, timedelta

from app.core.database import init_database, close_database, get_database_session
from app.models.orm_models import PipelineExecutionORM, PipelineExecutionLogORM, MVPProjectORM
from sqlalchemy import select

pytestmark = pytest.mark.asyncio


@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    from app.config.settings import settings
    try:
        setattr(settings, 'database_url', 'sqlite+aiosqlite:///./leanvibe_test.db')
        setattr(settings, 'is_development', True)
    except Exception:
        pass
    await init_database()
    yield
    await close_database()


async def _create_project_and_execution(tenant_id):
    project_id = uuid4()
    async for session in get_database_session():
        project = MVPProjectORM(
            id=project_id,
            tenant_id=tenant_id,
            project_name="Test Project",
            slug="test-project",
            description="desc",
            status="blueprint_pending",
        )
        session.add(project)
        exec_row = PipelineExecutionORM(
            mvp_project_id=project_id,
            tenant_id=tenant_id,
            current_stage="backend_development",
            status="initializing",
        )
        session.add(exec_row)
        await session.flush()
        await session.commit()
        return project_id, exec_row.id


async def _seed_logs(exec_id, tenant_id, project_id, entries):
    async for session in get_database_session():
        for e in entries:
            session.add(PipelineExecutionLogORM(
                execution_id=exec_id,
                tenant_id=tenant_id,
                mvp_project_id=project_id,
                timestamp=e["ts"],
                level=e["level"],
                message=e["msg"],
                stage=e.get("stage"),
            ))
        await session.flush()
        await session.commit()


async def test_logs_endpoint_filters_and_seek(monkeypatch):
    from app.api.endpoints.pipelines import get_pipeline_logs

    tenant_id = uuid4()
    project_id, exec_id = await _create_project_and_execution(tenant_id)

    base = datetime.utcnow() - timedelta(hours=1)
    entries = [
        {"ts": base + timedelta(minutes=1), "level": "INFO", "msg": "alpha", "stage": "backend"},
        {"ts": base + timedelta(minutes=2), "level": "ERROR", "msg": "beta", "stage": "backend"},
        {"ts": base + timedelta(minutes=3), "level": "INFO", "msg": "gamma", "stage": "frontend"},
        {"ts": base + timedelta(minutes=4), "level": "INFO", "msg": "alpha two", "stage": "frontend"},
        {"ts": base + timedelta(minutes=5), "level": "WARNING", "msg": "delta", "stage": "deployment"},
    ]
    await _seed_logs(exec_id, tenant_id, project_id, entries)

    # For seek, find anchor id at ts=+2 min (beta)
    async for session in get_database_session():
        res = await session.execute(select(PipelineExecutionLogORM).where(
            PipelineExecutionLogORM.execution_id == exec_id,
            PipelineExecutionLogORM.message == "beta"
        ))
        anchor = res.scalar_one()
        anchor_id = anchor.id
        break

    class DummyCred:
        credentials = "token"

    class DummyAuth:
        async def verify_token(self, token):
            return {"user_id": str(uuid4())}

    import app.api.endpoints.pipelines as pipelines_module
    monkeypatch.setattr(pipelines_module, "auth_service", DummyAuth())

    class DummyTenant:
        def __init__(self, id):
            self.id = id

    # Filter: start_time after first, level INFO only, search 'alpha', sort desc
    logs = await get_pipeline_logs(
        pipeline_id=project_id,
        credentials=DummyCred(),
        tenant=DummyTenant(tenant_id),
        limit=10,
        offset=0,
        level_filter="INFO",
        stage_filter=None,
        start_time=base + timedelta(minutes=1, seconds=1),
        end_time=None,
        search="alpha",
        sort="desc",
        after_id=None,
    )
    msgs = [l.message for l in logs]
    assert msgs == ["alpha two"]

    # Seek: after anchor (beta), asc order, no filters
    logs2 = await get_pipeline_logs(
        pipeline_id=project_id,
        credentials=DummyCred(),
        tenant=DummyTenant(tenant_id),
        limit=10,
        offset=0,
        level_filter=None,
        stage_filter=None,
        start_time=None,
        end_time=None,
        search=None,
        sort="asc",
        after_id=anchor_id,
    )
    msgs2 = [l.message for l in logs2]
    assert msgs2 == ["gamma", "alpha two", "delta"]


async def test_logs_summary_endpoint_counts(monkeypatch):
    from app.api.endpoints.pipelines import get_pipeline_logs_summary

    tenant_id = uuid4()
    project_id, exec_id = await _create_project_and_execution(tenant_id)

    base = datetime.utcnow() - timedelta(hours=1)
    entries = [
        {"ts": base + timedelta(minutes=1), "level": "INFO", "msg": "one", "stage": "backend"},
        {"ts": base + timedelta(minutes=2), "level": "ERROR", "msg": "two", "stage": "backend"},
        {"ts": base + timedelta(minutes=3), "level": "INFO", "msg": "three", "stage": "frontend"},
    ]
    await _seed_logs(exec_id, tenant_id, project_id, entries)

    class DummyCred:
        credentials = "token"

    class DummyAuth:
        async def verify_token(self, token):
            return {"user_id": str(uuid4())}

    import app.api.endpoints.pipelines as pipelines_module
    monkeypatch.setattr(pipelines_module, "auth_service", DummyAuth())

    class DummyTenant:
        def __init__(self, id):
            self.id = id

    summary = await get_pipeline_logs_summary(
        pipeline_id=project_id,
        credentials=DummyCred(),
        tenant=DummyTenant(tenant_id),
        start_time=None,
        end_time=None,
    )

    assert summary["total"] == 3
    assert summary["by_level"].get("INFO") == 2
    assert summary["by_level"].get("ERROR") == 1
    # Stages aggregated
    assert summary["by_stage"].get("backend") == 2
    assert summary["by_stage"].get("frontend") == 1
