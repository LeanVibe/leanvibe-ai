You are a senior Cursor Agent joining an ongoing LeanVibe codebase. Your mission is to finalize persistence, logs, RBAC/audit, storage providers, analytics, and tests/CI to production quality.

Context highlights:
- Backend: FastAPI with rich services; DB utilities in `app/core/database.py`; ORM models in `app/models/orm_models.py`.
- We migrated MVP Projects and Interviews to DB:
  - `app/services/mvp_service.py` uses DB first for MVPProject; persists generation progress JSON.
  - `app/api/endpoints/interviews.py` stores interview data in `MVPProjectORM.interview_data` (DB-first).
- Pipeline Execution persistence started:
  - `PipelineExecutionORM` and `PipelineExecutionLogORM` added; orchestration persists lifecycle events best-effort.
- Storage: endpoints now list/download/archive from a local storage abstraction; S3 not yet implemented.
- Frontend: Next.js App Router; dashboard shows live pipelines with Pause/Resume and logs panel; projects UI; interview wizard; Playwright smoke tests and Jest passing.

Your Objectives (in order):
1) Execution Logs – DB Write/Read
- Implement DB writes for pipeline logs in `mvp_service._add_log`: resolve `execution_id` (latest for project) and `tenant_id`; insert `PipelineExecutionLogORM` entries. Keep in-memory append for fallback.
- Update `/pipelines/{pipeline_id}/logs` to read DB-first with filters: level, stage, pagination (limit/offset), then fallback to in-memory logs. Ensure correct mapping to `PipelineLogEntry`.
- Add indexes if needed (already present in ORM). Validate with a minimal integration test.

2) Migrations
- Add Alembic migrations for:
  - `pipeline_executions` and `pipeline_execution_logs` (full schema, indexes).
  - Any missing indexes for `mvp_projects` used by new queries.
- Provide a README snippet on running migrations locally.

3) RBAC & Audit
- Define role policy helpers (founder, collaborator, admin). Integrate checks in key endpoints: `pipelines.py`, `mvp_projects.py`, `interviews.py`, `analytics.py`.
- Add audit writes (action, resource_type/id, metadata) for: pipeline pause/resume, downloads, approvals, and interview submit.
- Provide minimal tests (unit/integration) for permission denials and audit side-effects.

4) Storage Providers & Previews
- Implement S3 provider with presigned URLs and range support under `app/services/storage/s3_storage_service.py`.
- Introduce a simple provider interface (local|s3) with env-based selection.
- Frontend: add previews for text/markdown/images/logs in project detail; use signed URLs.

5) Analytics & Observability
- Ensure `monitoring.py` exposes pipeline/tenant metrics and websocket status as per docs; fill gaps.
- Add `/analytics` frontend page with charts; use existing tokens/hooks.

6) Testing & CI
- Backend: add small integration tests for DB persistence and logs; mock legacy ML imports to avoid external deps.
- Frontend: extend Playwright scenarios (auth, interview, pipeline start/pause/resume, file downloads) and Jest for new components.
- Add CI workflow (GitHub Actions) to run unit + e2e, enforce coverage thresholds, and upload artifacts.

Constraints & Notes:
- Respect existing coding style and patterns; retain in-memory fallbacks where used elsewhere.
- Don’t break current APIs; additive changes only.
- Avoid long-running background processes.

Where to start (files):
- DB logs write: `app/services/mvp_service.py` (`_add_log`) and latest `execution_id` lookup via `PipelineExecutionORM`.
- Logs read: `app/api/endpoints/pipelines.py` (`get_pipeline_logs`).
- Migrations: create Alembic revisions for new ORMs.
- RBAC/Audit: `app/auth/permissions.py`, `app/api/endpoints/*`, add `AuditLogORM` writes.
- Storage: `app/services/storage/*` (create S3 provider + interface), `mvp_projects.py` endpoints.
- Analytics: `app/api/endpoints/monitoring.py` and frontend `/analytics` pages.

Deliverables Checklist (must turn green):
- [ ] DB log writes wired; DB-first log reads with filters/pagination
- [ ] Alembic migrations created and documented
- [ ] RBAC enforcement and audit logging for critical actions
- [ ] S3 provider implemented; previews on frontend
- [ ] Analytics endpoints + frontend page
- [ ] Backend integration tests (no external ML deps); Frontend Playwright flows
- [ ] CI workflow with coverage and artifact uploads

Report progress in concise commits, keeping messages under 72 characters for the first line.
