import os
import asyncio
import pytest
from uuid import uuid4, UUID
from io import BytesIO

from app.api.endpoints.mvp_projects import download_project_archive, download_project_file, delete_project
from app.models.mvp_models import MVPProject, MVPStatus

pytestmark = pytest.mark.asyncio


class DummyCred:
    credentials = "token"


class DummyAuth:
    async def verify_token(self, token):
        return {"user_id": "test-user"}


class DummyTenant:
    def __init__(self, id: UUID):
        self.id = id


def _ensure_local_artifact(project_id: UUID, rel_path: str, content: bytes):
    base = os.path.abspath(os.path.join(os.getcwd(), "generated_artifacts", project_id.hex))
    os.makedirs(os.path.dirname(os.path.join(base, rel_path)), exist_ok=True)
    with open(os.path.join(base, rel_path), "wb") as f:
        f.write(content)


@pytest.fixture(autouse=True)
async def patch_auth(monkeypatch):
    import app.api.endpoints.mvp_projects as mod
    monkeypatch.setattr(mod, "auth_service", DummyAuth())
    # No-op audit
    class DummyAudit:
        async def log(self, **kwargs):
            return None
    monkeypatch.setattr(mod, "audit_service", DummyAudit())
    yield


@pytest.fixture
def deployed_project(monkeypatch):
    tenant_id = uuid4()
    project_id = uuid4()
    mvp = MVPProject(
        id=project_id,
        tenant_id=tenant_id,
        project_name="ZipTest",
        slug="ziptest",
        description="",
        status=MVPStatus.DEPLOYED,
    )
    import app.api.endpoints.mvp_projects as mod
    async def get_mvp_project(pid: UUID):
        return mvp if pid == project_id else None
    monkeypatch.setattr(mod.mvp_service, "get_mvp_project", get_mvp_project)
    return tenant_id, project_id


async def _collect_streaming_body(resp):
    # Consume StreamingResponse iterator to bytes
    chunks = []
    async for chunk in resp.body_iterator:  # type: ignore[attr-defined]
        chunks.append(chunk)
    return b"".join(chunks)


async def test_archive_zip_streams_local(deployed_project):
    tenant_id, project_id = deployed_project
    # seed files
    _ensure_local_artifact(project_id, "a.txt", b"alpha")
    _ensure_local_artifact(project_id, "dir/b.txt", b"bravo")

    resp = await download_project_archive(
        project_id=project_id,
        credentials=DummyCred(),
        tenant=DummyTenant(tenant_id),
        _perm=None,
        format="zip",
    )
    body = await _collect_streaming_body(resp)
    # very lightweight validation: zip header signature
    assert body[:2] == b"PK"
    assert len(body) > 100


async def test_preview_small_text_inline(deployed_project):
    tenant_id, project_id = deployed_project
    content = b"hello preview"
    _ensure_local_artifact(project_id, "readme.md", content)

    resp = await download_project_file(
        project_id=project_id,
        file_path="readme.md",
        credentials=DummyCred(),
        tenant=DummyTenant(tenant_id),
        _perm=None,
        preview=True,
        range_header=None,
    )
    # Inline disposition
    disp = resp.headers.get("content-disposition", "").lower()
    assert "inline" in disp
    assert b"".join([resp.body]) == content  # Response body is set for non-streaming


async def test_delete_project_cleans_artifacts(deployed_project):
    tenant_id, project_id = deployed_project
    _ensure_local_artifact(project_id, "to_remove.txt", b"bye")
    base_dir = os.path.join(os.getcwd(), "generated_artifacts", project_id.hex)
    assert os.path.isdir(base_dir)

    await delete_project(
        project_id=project_id,
        credentials=DummyCred(),
        tenant=DummyTenant(tenant_id),
        _perm=None,
    )

    # Directory should be removed (best-effort)
    assert not os.path.isdir(base_dir)
