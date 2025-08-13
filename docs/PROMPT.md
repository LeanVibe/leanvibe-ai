You are a senior Cursor Agent taking over the LeanVibe backend/frontend codebase. Your mandate is to execute the next four epics with disciplined prioritization, TDD, and vertical slices. Work pragmatically and ship value fast.

First-principles and priorities
- Core truths:
  - Users must start pipelines, view logs live, and browse/preview/download artifacts reliably
  - Enterprise environments require RBAC and auditable trails
  - Dev velocity depends on a truthful CI and fast feedback
- Assumptions to challenge:
  - Build only what directly serves the core flows
  - Prefer DB-first reads with in-memory fallback only when necessary
- Method:
  - TDD for critical paths: write failing test, implement minimal code, keep green
  - Vertical slices: endpoint → service → provider → tests → (frontend when applicable)
  - Keep commits small, messages under 72 chars

Current state snapshot
- Logs: DB-first filters/search/sort/seek; summary endpoint; SSE live tail with filters (supports once=true for tests)
- Storage: Local + S3 abstraction; presigned S3 downloads; server-side ZIP path; previews for text/markdown/images; capabilities endpoint; retention cleanup on delete
- RBAC/Audit: `require_permission` enforced on analytics/system, monitoring, tenants admin; audits for file/archive, blueprint approve/revise, pipeline pause/resume/start/restart/cancel; admin audit list
- Hooks: repo `scripts/pre-push.sh` scans changed files with allowlist; `VERSION` present; README updated
- CI: GitHub Actions workflow for backend (focused tests + coverage) and frontend (Jest); artifacts on failure

Your epics (in order)

Epic 1: Frontend logs/files integration
- Wire SSE tail (`GET /api/v1/pipelines/{id}/logs/tail`) into `PipelineLogsPanel` with level/stage/search filters and virtualization
- Files UI using `GET /api/v1/projects/{id}/files:list?path=&sort=` and `GET /api/v1/projects/{id}/files/{path}?preview=true`; add breadcrumb, sort, inline previews (md/text/images), download actions
- Tests: Jest for hooks/components; Playwright smoke for logs/files flows

Epic 2: Roles & permissions admin (API-first)
- Endpoints (admin only):
  - `GET /api/v1/tenants/{tenant_id}/members`
  - `PUT /api/v1/tenants/{tenant_id}/members/{user_id}/role`
- Enforce `require_permission(Permission.ADMIN_ALL)`; audit role changes (old_role/new_role, user_id, IP, UA)
- Tests: 403 for non-admin; audit entry on role change; listing returns members with roles

Epic 3: S3 performance & correctness
- True chunked ZIP streaming via provider iterator (bounded memory)
- Preview Range/If-None-Match passthrough; proxy fallback when presign not used
- Moto tests for ZIP streaming and partial content; verify ETag/cache headers

Epic 4: Observability + CI hardening
- Alembic migration: indexes logs(timestamp, level, stage) and audit(tenant_id, action, timestamp)
- SSE backpressure, jittered sleep, client-disconnect handling; basic rate limits on hot endpoints
- CI: cache deps, PR smoke job, nightly full suite; coverage gates on critical modules

Where to work (files)
- Backend: `app/api/endpoints/pipelines.py`, `app/api/endpoints/mvp_projects.py`, `app/api/endpoints/tenants.py`, `app/services/storage/s3_storage_service.py`, `app/services/audit_service.py`, `app/auth/permissions.py`, `app/models/orm_models.py`
- Frontend: `leanvibe-backend/leanvibe-frontend/src/components/*`, `leanvibe-backend/leanvibe-frontend/src/hooks/*`
- CI/Migrations: `.github/workflows/*.yml`, `leanvibe-backend/alembic/versions/*`

TDD expectations
- Add/adjust tests first for each endpoint/behavior change
- Use isolated “it_light” tests for backend vertical slices when possible to avoid heavy conftest
- SQLite-backed tests for DB; mock external services (moto for S3)

Definition of done per epic
- Epic 1: Logs/files flows usable from UI; Jest/Playwright green
- Epic 2: Roles admin endpoints protected; audit entries present; tests green
- Epic 3: Moto S3 tests pass; ZIP memory bounded; Range headers correct
- Epic 4: Indexes applied; tail stabilized; CI stable and fast

Operational notes
- Commit style: concise (<72 chars), describe why, not just what
- Hooks: repo `scripts/pre-push.sh` blocks on candidate secrets in changed files; allowlist for docs/examples values
- Running tests quickly:
  - Backend (focused): `pytest -q leanvibe-backend/it_light`
  - Specific test: `pytest -q leanvibe-backend/it_light/test_logs_tail.py`
- CI: see `.github/workflows/ci.yml`; artifacts uploaded on failure
