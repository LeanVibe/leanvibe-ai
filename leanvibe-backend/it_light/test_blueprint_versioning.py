import os, sys, pytest
sys.path.insert(0, os.path.abspath("leanvibe-backend"))
os.environ.setdefault("LEANVIBE_DATABASE_URL", "sqlite+aiosqlite:///./leanvibe_test.db")
os.environ.setdefault("LEANVIBE_SECRET_KEY", "test_secret_key")

from uuid import uuid4
from datetime import datetime

from app.api.endpoints.mvp_projects import update_project_blueprint, get_blueprint_history
from app.models.mvp_models import MVPProject, MVPStatus, TechnicalBlueprint, MVPProjectUpdateRequest, BlueprintUpdateRequest, FounderInterview, MVPTechStack
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


async def test_blueprint_versioning_history(monkeypatch):
    project_id = uuid4()
    tenant_id = uuid4()
    # Seed project with initial blueprint
    proj = MVPProject(
        id=project_id,
        tenant_id=tenant_id,
        project_name="BP",
        slug="bp",
        description="",
        status=MVPStatus.BLUEPRINT_PENDING,
        interview=FounderInterview(
            business_idea="a",
            target_market="b",
            value_proposition="c",
            problem_statement="p",
            target_audience="devs",
            core_features=["f1"],
        ),
        blueprint=TechnicalBlueprint(
            tech_stack=MVPTechStack.API_ONLY,
            architecture_pattern="monolith",
            database_schema={},
            api_endpoints=[],
            user_flows=[],
            wireframes=[],
            design_system={},
            deployment_config={},
            monitoring_config={},
            scaling_config={},
            test_strategy={},
            performance_targets={},
            security_requirements=[],
            confidence_score=0.8,
            estimated_generation_time=1,
        ),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    mvp_service._projects_storage[project_id] = proj

    import app.api.endpoints.mvp_projects as mod
    monkeypatch.setattr(mod, "auth_service", DummyAuth())

    # Update blueprint -> should record previous version
    req = BlueprintUpdateRequest(blueprint=TechnicalBlueprint(
        tech_stack=MVPTechStack.API_ONLY,
        architecture_pattern="services",
        database_schema={},
        api_endpoints=[],
        user_flows=[],
        wireframes=[],
        design_system={},
        deployment_config={},
        monitoring_config={},
        scaling_config={},
        test_strategy={},
        performance_targets={},
        security_requirements=[],
        confidence_score=0.9,
        estimated_generation_time=2,
    ))
    resp = await update_project_blueprint(
        project_id=project_id,
        update_request=req,
        credentials=DummyCred(),
        tenant=DummyTenant(tenant_id),
        _perm=None,
    )
    assert resp.blueprint.architecture_pattern == "services"

    # History should contain both versions (old then new at end)
    history = await get_blueprint_history(
        project_id=project_id,
        credentials=DummyCred(),
        tenant=DummyTenant(tenant_id),
        _perm=None,
    )
    assert len(history) >= 2
    assert history[-1].blueprint.architecture_pattern == "services"