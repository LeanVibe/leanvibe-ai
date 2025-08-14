# LeanVibe – Implementation Plan (Focused, TDD, Vertical Slices)

Scope: deliver the core user journeys with the minimum software that is reliable, observable, and permissioned.

Guiding principles
- TDD for critical paths (endpoint behavior, persistence, security checks)
- Vertical slices: API → service → provider → tests → docs
- YAGNI: only what directly serves the core journey
- Keep commits small and messages under 72 chars

Current state (as of this commit)
- Pre-push: repo `scripts/pre-push.sh` scans changed files; integrated in local pre-push; README updated; VERSION=0.1.0
- Storage: local streaming, S3 presign; server-side ZIP (local, S3-provider path); preview (text/markdown/images); retention cleanup on delete
- Logs: DB-first filters/seek/summary; SSE live tail with filters (`once=true` for tests)
- RBAC/Audit: admin perms enforced across monitoring/tenants; audit for file/archive, pipeline pause/resume/start/restart/cancel; analytics export; blueprint revision/approve; admin audit list endpoint
- CI: GitHub Actions added (backend focused tests + coverage >=65%; frontend jest; artifacts on failure)

Next 4 epics (detailed)

Epic 1: Frontend logs/files integration (must-have UX)
- Goals
  - Logs panel uses SSE tail with level/stage/search filters and virtualization
  - Files view lists directories, supports inline previews (md/text/images), and downloads
- API hooks to use
  - `GET /api/v1/pipelines/{id}/logs/tail` (SSE; supports once=true for tests)
  - `GET /api/v1/projects/{id}/files:list?path=&sort=` (directory listing)
  - `GET /api/v1/projects/{id}/files/{path}?preview=true`
- Work items
  - Add `use-logs-tail` hook: connects SSE, exposes `pause/resume`, filters
  - Update `PipelineLogsPanel.tsx`: sticky filters, virtualized list, copy-to-clipboard, jump-to-last
  - Add Files page: breadcrumb + sort + preview pane; download button; empty states
  - Tests: Jest for hooks/components; Playwright smoke (open logs; switch filters; open file preview)
- Acceptance
  - Logs stream in real-time; filters applied client-side without jitter
  - Files list renders quickly; inline previews for small text/md/images; downloads work

Epic 2: Roles & permissions admin (API-first)
- Goals
  - Admins can list tenant members and update member roles
  - All role changes audited
- Endpoints
  - `GET /api/v1/tenants/{id}/members` (admin only)
  - `PUT /api/v1/tenants/{id}/members/{user_id}/role` (admin only)
- Work items
  - Implement read/update on `TenantMemberORM` with `require_permission(Permission.ADMIN_ALL)`
  - Audit entries for role changes: action=`tenant_role_change`, include old_role/new_role, user_id/ip/ua if available
  - Tests: 403 for non-admin; successful role update writes audit row; listing returns members with roles
- Acceptance
  - Non-admins see 403; admin updates persist and are auditable

Epic 3: S3 performance and correctness (provider depth)
- Goals
  - Server-side ZIP uses true chunked reads; keep memory bounded
  - Previews honor Range/If-None-Match; proxy fallback when presign unavailable
- Work items
  - In `s3_storage_service.py`: add chunked `iter_object(key, chunk_size)`; use it to feed a streaming zip writer
  - In `mvp_projects.py`: for S3 preview, forward Range and ETag headers when proxying
  - Moto tests: ZIP of 3 objects (assert ZIP signature, entries present); Range 206 partial for a large text blob; ETag passthrough
- Acceptance
  - Large archives do not OOM; Range works; headers correct

Epic 4: Observability + CI hardening (operational)
- Goals
  - DB indexes for logs/audit; SSE backpressure; rate limits on hot endpoints
  - CI more reliable and fast
- Work items
  - Alembic migration adding indexes: logs(timestamp, level, stage), audit(tenant_id, action, timestamp)
  - SSE tail: configurable max loop iterations, jittered sleep, early close on client disconnect
  - Simple rate-limit dependency for tail and heavy list endpoints (per-IP token bucket)
  - CI: cache dependencies, add PR smoke job, nightly full suite; fail on coverage drop in critical modules
- Acceptance
  - Noticeable latency reduction on logs queries; no SSE runaway loops; CI stable and informative

How to work
- Prefer isolated “it_light” tests for vertical slices that sidestep heavy conftest
- Mock external deps (S3 via moto; SSE with `once=true`)
- Keep endpoints additive; avoid breaking existing consumers
- Commit small and push after each epic

File map (touchpoints)
- Backend
  - `app/api/endpoints/pipelines.py` (SSE/logs)
  - `app/api/endpoints/mvp_projects.py` (files/list/preview/archive)
  - `app/api/endpoints/tenants.py` (roles admin endpoints)
  - `app/services/storage/s3_storage_service.py` (chunked reads)
  - `app/services/audit_service.py`, `app/auth/permissions.py`, `app/models/orm_models.py`
  - Alembic migrations under `leanvibe-backend/alembic/versions/*`
- Frontend
  - `leanvibe-backend/leanvibe-frontend/src/components/pipelines/*`
  - `leanvibe-backend/leanvibe-frontend/src/hooks/*`

Definition of done per epic
- Frontend logs/files: smoke flows pass; UX responsive; tests green
- Roles admin: endpoints protected; audit entries present; tests green
- S3 perf: moto tests pass; memory bounded; headers correct
- Observability/CI: indexes present; SSE/rate limit in place; CI stable

Status (as of this commit)
- Epic 1: DONE. SSE tail integrated in UI with client filters; files UI with previews and downloads; Jest + it_light tests green.
- Epic 2: DONE. Admin list/update member role endpoints with audits.
- Epic 3: DONE. S3 `iter_object`; bounded ZIP streaming; SSE jitter.
- Epic 4: PARTIAL. Index migration added; rate limit on SSE tail; remaining: early disconnect handling and CI consolidation (nightly + coverage gates).
  - Update: SSE early disconnect now handled in pipelines tail; remaining: CI consolidation and Playwright smoke.

Immediate next tasks (high value, low risk)
- SSE early disconnect in `pipelines.tail_pipeline_logs` by detecting client disconnect and exiting generator.
- Playwright smoke tests for logs panel and file preview (basic path).
- CI consolidation: merge duplicate job sets and ensure caching across workflows.

