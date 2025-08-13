You are a senior Cursor Agent taking over an ongoing LeanVibe backend/frontend codebase. Your mandate is to finish the next four epics with disciplined prioritization, TDD, and vertical slices. Work pragmatically and ship value fast.

First-principles and priorities
- Core truths:
  - Users must start pipelines, view progress/logs, and download artifacts reliably.
  - Enterprise environments require RBAC and auditable trails.
  - Dev velocity depends on reliable pushes and a fast, truthful CI.
- Assumptions to challenge:
  - Only build features directly needed by core flows; avoid speculative complexity.
  - Prefer DB-first reads with in-memory fallback only when necessary.
- Method:
  - TDD for critical paths: write failing test, implement minimal code, keep green.
  - Vertical slices: endpoint → service → storage/DB → tests.
  - Keep commits small, messages under 72 chars.

Current state snapshot
- Logs: DB write via `mvp_service._add_log` best-effort; DB-first read with filters/search/sort/seek; summary endpoint. Integration tests exist (`tests/integration/test_pipeline_logs_filters.py`).
- Storage: Local + S3 abstraction; presigned S3 downloads; archives use provider abstraction; capabilities endpoint added.
- RBAC/Audit: `require_permission` fixed; applied to key endpoints; audits for file download/archive/blueprint approve and pipeline pause/resume.
- Global pre-push hook: fixed to use repo root and tracked-only scans; still flags tracked credential patterns. Further tuning needed.

Your epics (in order)

Epic 0: Pre-push reliability (quick win)
- Restrict credential scans to changed files by default: use `git diff --cached --name-only` and `git grep` over that set; fallback to all tracked with env `STRICT_PREPUSH=1`.
- Add allowlist for docs/examples (`docs/**`, `**/examples/**`) with non-secret placeholder values (e.g., `password=example`).
- Add `VERSION` file with `0.1.0`.
- Document `hooks` behavior in README.

Epic 1: Storage: S3 ZIP streaming + previews + cleanup
- Implement server-side ZIP streaming for S3 in `mvp_projects.py/download_project_archive`:
  - Iterate provider `list_files(project_id)`, stream each object via chunked `get_object` to a `zipstream`-style writer or Python `zipfile` with a file-like that fetches chunks (keep memory bounded).
  - Ensure content-disposition and audit log.
- Preview endpoint for small files: `GET /api/v1/projects/{id}/files/{path}?preview=true`
  - For text/markdown/logs under e.g., 1MB: inline `Content-Disposition`, correct MIME; S3: support `Range` header and forward partial response.
- Retention: on project delete, call provider to delete all under project prefix (implement for Local + S3). Wire into `delete_project` in `mvp_projects.py`.
- Tests: integration tests for ZIP streaming (local; S3 mocked), preview for small text/markdown, delete cleanup.

Epic 2: RBAC & Audit breadth
- Replace TODO admin checks in `analytics.system`, `monitoring.py` endpoints, and `tenants.py` admin operations with `require_permission`.
- Audit events: pipeline start/restart/cancel; blueprint revision request; analytics export; tenant role changes. Include `user_id`, IP, UA if available.
- Admin audit list endpoint: `GET /api/v1/audit` with filters and pagination.
- Tests: permission denials and audit entries creation.

Epic 3: CI baseline
- GitHub Actions to run:
  - Backend: setup Python, `alembic upgrade head`, run focused tests (skip archived/legacy); coverage >= 65%.
  - Frontend: `npm ci`, Jest, Playwright smoke.
  - Upload artifacts on failure.
- Add `scripts/pre-push.sh` mirroring repo-specific checks; document replacing global hook.

Where to work (files)
- Hooks: `~/.config/git/hooks/pre-push` (global), `scripts/pre-push.sh`, `README.md`.
- Storage: `app/services/storage/*`, `app/api/endpoints/mvp_projects.py`.
- Logs: `app/api/endpoints/pipelines.py`, tests under `leanvibe-backend/tests/integration/*`.
- RBAC/Audit: `app/auth/permissions.py`, `app/api/endpoints/*`, `app/services/audit_service.py`, `app/models/orm_models.py`.
- CI: `.github/workflows/*.yml` (create), `pyproject.toml`/`pytest.ini` filter patterns.

TDD expectations
- For each endpoint behavior change, add/adjust tests first.
- Keep tests self-contained, SQLite-backed for DB, and mock external services (e.g., boto3 S3).

Definition of done per epic
- Epic 0: `git push` passes pre-push without `--no-verify` on a clean repo; README notes updated.
- Epic 1: ZIP streaming works on S3 + Local; previews work; delete cleans artifacts; tests green.
- Epic 2: RBAC coverage complete; audit events emitted; admin audit list present; tests green.
- Epic 3: CI pipelines green on main; failing PRs block merges.

Reporting
- Keep commit messages descriptive and under 72 chars.
- Summarize what changed and why in PR body.
