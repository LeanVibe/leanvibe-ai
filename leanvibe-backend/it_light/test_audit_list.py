import os, sys, pytest
sys.path.insert(0, os.path.abspath("leanvibe-backend"))
os.environ.setdefault("LEANVIBE_DATABASE_URL", "sqlite+aiosqlite:///./leanvibe_test.db")
os.environ.setdefault("LEANVIBE_SECRET_KEY", "test_secret_key")

from uuid import uuid4
from datetime import datetime

from app.api.endpoints.audit import list_audit_logs
from app.services.audit_service import audit_service

pytestmark = pytest.mark.asyncio


class DummyAdmin:
    async def __call__(self):
        return {"permissions": ["admin:all"]}


async def test_audit_list_returns_entries(monkeypatch):
    tenant_id = uuid4()
    # Seed two audit entries
    await audit_service.log(
        tenant_id=tenant_id,
        action="pipeline_start",
        resource_type="pipeline",
        resource_id=str(uuid4()),
        details={"note": "start"},
    )
    await audit_service.log(
        tenant_id=tenant_id,
        action="analytics_export",
        resource_type="analytics",
        resource_id="export_123",
        details={"format": "csv"},
    )

    # Bypass permission dependency in test by monkeypatching require
    import app.api.endpoints.audit as mod
    async def allow_admin(*args, **kwargs):
        return {"permissions": ["admin:all"]}
    monkeypatch.setattr(mod, "require_permission", lambda perm: allow_admin)

    result = await list_audit_logs(
        tenant_id=tenant_id,
        action=None,
        resource=None,
        user_id=None,
        start_time=None,
        end_time=None,
        limit=10,
        offset=0,
        _admin=None,
    )
    assert result["total"] >= 2
    assert any(item["action"] == "pipeline_start" for item in result["items"])