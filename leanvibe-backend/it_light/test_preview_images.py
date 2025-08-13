import os, sys, pytest
sys.path.insert(0, os.path.abspath("leanvibe-backend"))
os.environ.setdefault("LEANVIBE_DATABASE_URL", "sqlite+aiosqlite:///./leanvibe_test.db")
os.environ.setdefault("LEANVIBE_SECRET_KEY", "test_secret_key")

from uuid import uuid4
from app.api.endpoints.mvp_projects import download_project_file
from app.models.mvp_models import MVPProject, MVPStatus, FounderInterview
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


def _seed_project(project_id, tenant_id):
    proj = MVPProject(
        id=project_id,
        tenant_id=tenant_id,
        project_name="P",
        slug="p",
        description="",
        status=MVPStatus.DEPLOYED,
        interview=FounderInterview(
            business_idea="a",
            target_market="b",
            value_proposition="c",
            problem_statement="p",
            target_audience="devs",
            core_features=["f1"],
        ),
    )
    mvp_service._projects_storage[project_id] = proj


def _ensure_local_artifact(project_id, rel_path, content: bytes):
    base = os.path.abspath(os.path.join(os.getcwd(), "generated_artifacts", project_id.hex))
    os.makedirs(os.path.dirname(os.path.join(base, rel_path)), exist_ok=True)
    with open(os.path.join(base, rel_path), "wb") as f:
        f.write(content)


async def test_preview_small_image_inline(monkeypatch):
    project_id = uuid4()
    tenant_id = uuid4()
    _seed_project(project_id, tenant_id)

    # Minimal PNG header bytes
    png_bytes = b"\x89PNG\r\n\x1a\n" + b"0" * 100
    _ensure_local_artifact(project_id, "img/test.png", png_bytes)

    import app.api.endpoints.mvp_projects as mod
    monkeypatch.setattr(mod, "auth_service", DummyAuth())

    resp = await download_project_file(
        project_id=project_id,
        file_path="img/test.png",
        credentials=DummyCred(),
        tenant=DummyTenant(tenant_id),
        _perm=None,
        preview=True,
        range_header=None,
    )
    assert resp.headers.get("content-disposition", "").lower().startswith("inline")
    assert resp.media_type.startswith("image/")
