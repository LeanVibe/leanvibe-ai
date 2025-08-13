import os
import sys
import pytest
from uuid import uuid4, UUID
from io import BytesIO

# Ensure backend package import
sys.path.insert(0, os.path.abspath("leanvibe-backend"))
# Force lightweight async sqlite to satisfy imports
os.environ.setdefault("LEANVIBE_DATABASE_URL", "sqlite+aiosqlite:///./leanvibe_test.db")
os.environ.setdefault("LEANVIBE_SECRET_KEY", "test_secret_key")

from app.api.endpoints.mvp_projects import download_project_archive, download_project_file
from app.models.mvp_models import MVPProject, MVPStatus

pytestmark = pytest.mark.asyncio


class DummyCred:
    credentials = "token"


class DummyAuth:
    async def verify_token(self, token):
        return {"user_id": "test-user"}


class DummyAudit:
    async def log(self, **kwargs):
        return None


class DummyTenant:
    def __init__(self, id: UUID):
        self.id = id


class FakeS3:
    def __init__(self, files):
        self._files = files

    def list_files(self, project_id: UUID):
        return self._files

    def get_file(self, project_id: UUID, rel_path: str):
        return BytesIO(b"content"), "application/octet-stream"

    def delete_project_artifacts(self, project_id: UUID):
        return None


class StoredFile:
    def __init__(self, path: str, size: int = 7, content_type: str = "application/octet-stream", modified_at=None):
        self.path = path
        self.size = size
        self.content_type = content_type
        self.modified_at = modified_at


@pytest.fixture(autouse=True)
def patch_services(monkeypatch):
    import app.api.endpoints.mvp_projects as mod
    monkeypatch.setattr(mod, "auth_service", DummyAuth())
    monkeypatch.setattr(mod, "audit_service", DummyAudit())
    yield


@pytest.fixture
def deployed_project(monkeypatch):
    tenant_id = uuid4()
    project_id = uuid4()
    mvp = MVPProject(
        id=project_id,
        tenant_id=tenant_id,
        project_name="S3Zip",
        slug="s3zip",
        description="",
        status=MVPStatus.DEPLOYED,
    )
    import app.api.endpoints.mvp_projects as mod
    async def get_mvp_project(pid: UUID):
        return mvp if pid == project_id else None
    monkeypatch.setattr(mod.mvp_service, "get_mvp_project", get_mvp_project)
    return tenant_id, project_id


async def _collect_streaming_body(resp):
    chunks = []
    async for chunk in resp.body_iterator:  # type: ignore[attr-defined]
        chunks.append(chunk)
    return b"".join(chunks)


async def test_archive_zip_streams_s3_mock(deployed_project, monkeypatch):
    tenant_id, project_id = deployed_project

    # Patch mvp_projects to treat our fake as S3StorageService instance
    import app.api.endpoints.mvp_projects as mod
    # Build a fake class to mirror the internal alias in module under test
    class FakeS3StorageService:
        pass
    # Also monkeypatch the imported alias in module scope, if present
    mod._S3Cls = FakeS3StorageService  # type: ignore

    files = [StoredFile("one.txt"), StoredFile("dir/two.txt")]
    class StorageImpl(FakeS3StorageService, FakeS3):
        pass
    storage = StorageImpl(files)
    monkeypatch.setattr(mod, "get_storage_service", lambda: storage)

    resp = await download_project_archive(
        project_id=project_id,
        credentials=DummyCred(),
        tenant=DummyTenant(tenant_id),
        _perm=None,
        format="zip",
    )
    body = await _collect_streaming_body(resp)
    assert body[:2] == b"PK"


async def test_s3_download_redirect_mock(deployed_project, monkeypatch):
    tenant_id, project_id = deployed_project
    import app.api.endpoints.mvp_projects as mod
    class FakeS3StorageService:
        pass
    mod._S3Cls = FakeS3StorageService  # type: ignore

    class RedirectingS3(FakeS3, FakeS3StorageService):
        def presign_download(self, project_id: UUID, rel_path: str, *, range_header=None) -> str:
            return "https://example.com/presigned"

    storage = RedirectingS3([StoredFile("readme.md")])
    monkeypatch.setattr(mod, "get_storage_service", lambda: storage)

    resp = await download_project_file(
        project_id=project_id,
        file_path="readme.md",
        credentials=DummyCred(),
        tenant=DummyTenant(tenant_id),
        _perm=None,
        preview=False,
        range_header=None,
    )
    assert resp.status_code == 307
    assert resp.headers.get("Location", "").startswith("https://example.com/")
