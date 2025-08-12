import os
os.environ.setdefault("LEANVIBE_DATABASE_URL", "sqlite+aiosqlite:///./leanvibe_test.db")
os.environ.setdefault("LEANVIBE_SECRET_KEY", "test_secret_key")

import pytest
import pytest_asyncio
import asyncio
from uuid import uuid4
from datetime import datetime

from app.core.database import init_database, close_database
from app.models.orm_models import PipelineExecutionORM, PipelineExecutionLogORM, MVPProjectORM
from app.services.mvp_service import mvp_service
from app.core.database import get_database_session
from sqlalchemy import select

pytestmark = pytest.mark.asyncio


@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    # Force SQLite async for tests
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
    # Create MVP project row
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
            current_stage="blueprint_generation",
            status="initializing",
        )
        session.add(exec_row)
        await session.flush()
        await session.commit()
        return project_id, exec_row.id


async def test_mvp_service_add_log_persists_to_db():
    tenant_id = uuid4()
    project_id, exec_id = await _create_project_and_execution(tenant_id)

    # Add two logs via service API
    mvp_service._add_log(project_id, level="info", message="one", stage="backend")
    mvp_service._add_log(project_id, level="ERROR", message="two", stage="deployment")

    # Give async task loop a moment
    await asyncio.sleep(0.05)

    # Verify DB has logs
    async for session in get_database_session():
        res = await session.execute(select(PipelineExecutionLogORM).where(PipelineExecutionLogORM.execution_id == exec_id))
        rows = res.scalars().all()
        assert len(rows) >= 2
        levels = {r.level for r in rows}
        assert "INFO" in levels and "ERROR" in levels


async def test_logs_endpoint_reads_db_first(monkeypatch):
    from app.api.endpoints.pipelines import get_pipeline_logs
    from fastapi import HTTPException

    tenant_id = uuid4()
    project_id, exec_id = await _create_project_and_execution(tenant_id)

    # Seed one DB log directly
    async for session in get_database_session():
        session.add(PipelineExecutionLogORM(
            execution_id=exec_id,
            tenant_id=tenant_id,
            mvp_project_id=project_id,
            level="INFO",
            message="db seeded",
            stage="backend",
        ))
        await session.flush()
        await session.commit()

    # Also seed in-memory logs to detect DB-first behavior
    mvp_service._add_log(project_id, level="INFO", message="memory only", stage="backend")
    await asyncio.sleep(0.02)

    # Mock auth and tenant dependency for endpoint call
    class DummyCred:
        credentials = "token"

    class DummyAuth:
        async def verify_token(self, token):
            return {"user_id": str(uuid4())}

    # Replace the auth_service used inside pipelines module
    import app.api.endpoints.pipelines as pipelines_module
    monkeypatch.setattr(pipelines_module, "auth_service", DummyAuth())

    # Simulate dependency-injected tenant
    class DummyTenant:
        def __init__(self, id):
            self.id = id

    # Call endpoint
    logs = await get_pipeline_logs(
        pipeline_id=project_id,
        credentials=DummyCred(),
        tenant=DummyTenant(tenant_id),
        limit=10,
        offset=0,
        level_filter=None,
        stage_filter=None,
    )

    # Should return the DB seeded log (db-first) and not rely on memory fallback
    assert any(l.message == "db seeded" for l in logs)
