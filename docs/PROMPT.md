You are a senior Cursor Agent taking over the LeanVibe codebase to complete Observability/CI hardening and polish remaining items. Use disciplined vertical slices, TDD for critical paths, and ship pragmatic value fast.

First-principles and priorities
- Core truths:
  - Users must view live logs and browse/preview/download artifacts reliably
  - Enterprise requires RBAC and auditable changes
  - Dev velocity depends on honest CI and fast feedback
- Assumptions to challenge:
  - Build only what directly serves core flows
  - Prefer DB-first reads; fall back to in-memory only when necessary (tests)
- Method:
  - TDD for critical paths; keep tests green
  - Vertical slices: endpoint → service → provider → tests → (frontend)
  - Small commits (<72 chars), focused messages on why

Current state snapshot
- Frontend: Logs panel on SSE (JSON, token query), client filters and auto-scroll; Files UI with directory listing, breadcrumb/sort, inline previews (md/text/images), and downloads; Jest green
- Backend: SSE tail with token query; S3 `iter_object`; bounded ZIP streaming; admin endpoints for tenant members list + role update with audits; DB-first log endpoints
- Observability: SSE jitter added; simple per-IP rate limit on logs tail; Alembic migration adds indexes for logs/audit
- CI: Multiple workflows present; some duplication; coverage gates pending

Immediate priorities (next 4 epics)
1) Observability polish (SSE)
   - Detect client disconnect in `app/api/endpoints/pipelines.py:tail_pipeline_logs` and exit generator early (keep jitter and once=true)
   - Keep token-based SSE auth path; maintain client-side filters
   - Add Playwright smoke: open logs panel, toggle filters; no flakiness (retry-friendly)
2) CI consolidation and coverage
   - Unify `.github/workflows/ci.yml` and `ci-cd.yml` (or make one delegate to the other)
   - Enable pip/npm caching; ensure coverage gates on `app/api/endpoints/*` and `app/services/storage/*`
   - Add nightly full suite and PR smoke job; upload artifacts on failure
3) S3 preview correctness
   - When proxying preview (non-presign) in `mvp_projects.download_project_file`, forward `Range` and `If-None-Match`; include ETag/cache headers
   - Add Moto tests for partial content (206) and ETag verification
4) Admin UI for roles (minimal frontend)
   - Add an admin screen to list tenant members and update roles; guard with `ADMIN_ALL`
   - Jest tests for hooks/components; basic e2e happy path

Where to work (files)
- Backend: `app/api/endpoints/pipelines.py`, `app/api/endpoints/mvp_projects.py`, `app/api/endpoints/tenants.py`, `app/services/storage/s3_storage_service.py`, `app/services/audit_service.py`, `app/auth/rate_limit.py`
- Frontend: `leanvibe-backend/leanvibe-frontend/src/components/*`, `leanvibe-backend/leanvibe-frontend/src/hooks/*`
- CI/Migrations: `.github/workflows/*.yml`, `leanvibe-backend/alembic/versions/*`

TDD expectations
- Write/adjust tests first for each behavior change
- Use `leanvibe-backend/it_light` for vertical slices; SQLite-backed; mock external services (Moto for S3)

Definition of done
- Observability: SSE stabilized (disconnect + jitter), rate limits on hot endpoints; Playwright smoke added
- CI: consolidated, cached; nightly + PR smoke; coverage gates on critical modules
- S3: partial-content and ETag behavior verified with Moto; ZIP memory bounded

Operational notes
- Commit style: concise (<72 chars), describe why
- Pre-push: `leanvibe-backend/.githooks/pre-push` runs quality gates (warn); `scripts/pre-push.sh` blocks on secrets for changed files (allowlisted placeholders and env-substitution lines are ignored)
- Run tests quickly:
  - Backend (focused): `pytest -q leanvibe-backend/it_light`
  - Specific: `pytest -q leanvibe-backend/it_light/test_logs_tail.py`
  - Frontend Jest: `npm test --prefix leanvibe-backend/leanvibe-frontend`
