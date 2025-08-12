# LeanVibe – Next Implementation Plan (Persistence, Logs, Tests, CI)

This plan fills the remaining gaps to productionize persistence, logging, analytics, and testing. It is designed for incremental delivery; each section has acceptance criteria and validation steps.

## 1) Persistence: Interviews, Pipelines, Executions, Logs

Scope:
- DB-backed storage for all entities currently using in-memory fallbacks.
- DB-first reads; in-memory only as a resilience fallback.

Tasks:
- Interviews
  - Already persisted as `MVPProjectORM.interview_data` on create/update/validate/submit.
  - Acceptance: list/get return DB-backed data; updates persisted; fallback path works when DB unavailable.
- MVP Projects
  - Already implemented DB save/update/get/list in `mvp_service` with fallbacks.
  - Persist realtime progress JSON on updates.
- Pipeline Executions
  - Add ORM: `PipelineExecutionORM` (done); write lifecycle events (start, transitions, completion) (done best‑effort).
  - Persist per‑stage overall/current progress and durations.
  - Acceptance: Pipeline restarts reflect last known execution state.
- Execution Logs
  - Add ORM: `PipelineExecutionLogORM` (done).
  - Persist logs: write from `mvp_service._add_log` by resolving `execution_id` (latest for project) and `tenant_id`.
  - Read logs in `/pipelines/{id}/logs` DB‑first with filters and pagination; fallback to in‑memory logs.

Validation:
- Manual: start pipeline → observe DB rows for execution + logs; pause/resume survives restart.
- Automated: minimal integration tests to assert DB writes/readbacks for projects, interviews, executions, and logs.

## 2) Migrations & Schema Management

Scope:
- Introduce Alembic migrations for new tables/columns.

Tasks:
- Create Alembic revision(s) for `pipeline_executions`, `pipeline_execution_logs` and any index additions.
- Ensure `MVPProjectORM` indexes exist; backfill step optional.

Validation:
- Fresh DB bootstraps via migrations; upgrade/downgrade works locally.

## 3) RBAC, Permissions, Audit

Scope:
- Enforce role‑based access in endpoints and log sensitive events.

Tasks:
- Define roles (founder, collaborator, admin) and policy helpers.
- Enforce in `pipelines.py`, `mvp_projects.py`, `interviews.py`, `analytics.py` where TODOs exist.
- Audit log writes (download, pause/resume, approvals).

Validation:
- Permission tests for each protected endpoint; audit entries visible in admin view.

## 4) Storage Providers & Artifact Lifecycle

Scope:
- Storage abstraction with S3 provider alongside local FS.

Tasks:
- Implement S3 storage (presigned URL, range requests), configurable via env.
- Wire `mvp_projects` endpoints to provider interface; keep local provider for dev.
- Add retention policy, background cleanup job.
- Frontend: add file previews (text/markdown/images/logs) using inline viewers.

Validation:
- S3 listing/download/archive functional; large files stream; range requests tested.

## 5) Analytics & Observability

Scope:
- Dashboards for pipeline performance, tenant usage, WebSocket health.

Tasks:
- Ensure endpoints in `monitoring.py` expose aggregate metrics; fill gaps.
- Frontend pages under `/analytics` to visualize charts.
- Budget/alert banners when error budgets exceeded.

Validation:
- Charts render live data; simple alert banners show when thresholds exceeded.

## 6) Testing & CI

Scope:
- Expand Jest and Playwright; add backend integration tests; CI gates.

Tasks:
- Frontend: more unit tests for new components (file browser, wizard); expand Playwright flows (auth, interview, pipeline lifecycle, downloads).
- Backend: minimal integration tests that run without external ML deps; mock out legacy imports; add DB fixtures using SQLite/aiosqlite.
- CI: coverage thresholds; run unit and e2e; artifact uploads (screenshots, videos).

Validation:
- CI green; coverage thresholds enforced; PRs show checks/results.

## 7) Performance & Hardening

Scope:
- Query performance, pagination, indexes; large log volumes.

Tasks:
- Indexes for logs by execution/time; efficient pagination (seek/ID > last) if needed.
- Batching for log inserts (optional); backpressure in WS broadcasting.

Validation:
- Load test on logs and pipeline events without timeouts.

---

Work Sequencing
1. Finish DB‑backed execution logs (write & read) and migrations.
2. RBAC + audit for critical endpoints.
3. Storage provider S3 and previews.
4. Analytics pages; Playwright tests and CI gates.

Deliverables Checklist
- [ ] DB log write path in `mvp_service._add_log`
- [ ] `/pipelines/{id}/logs` DB‑first reads with filters/pagination
- [ ] Alembic migrations for new execution/log tables
- [ ] Minimal backend integration tests
- [ ] RBAC enforcement + audit writes
- [ ] S3 provider + previews
- [ ] Analytics UI + tests
- [ ] CI configured with coverage and e2e
