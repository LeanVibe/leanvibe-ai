# LeanVibe – Implementation Plan (Focused, TDD, Vertical Slices)

This plan is trimmed to the 20% of work that delivers 80% of value for the core user journeys: creating and running pipelines, accessing files/artifacts, viewing logs/analytics, and enforcing permissions/compliance.

Guiding principles
- TDD for all critical paths (endpoint behavior, persistence, security checks)
- Vertical slices end-to-end per feature; ship working software each commit
- YAGNI: build only what is immediately required by the user journey

Epic 0: Pre-push reliability and security checks (must-have for developer velocity)
Scope:
- Ensure normal `git push` works reliably with meaningful validations; remove false positives.

Tasks:
- Fix global pre-push hook (done):
  - Detect repo root via `git rev-parse --show-toplevel` (instead of hooks dir)
  - Scan only tracked files via `git ls-files` and `git grep`, not full FS
- Remaining items to complete:
  - Restrict credential-grep to changed files by default (fallback: all tracked with an env toggle)
  - Add a tiny allowlist for patterns in docs/examples (e.g. “password=example” within `docs/**`)
  - Add `VERSION` file to satisfy version check (semantic version like `0.1.0`)
  - Document how to run validations locally and how to bypass in CI (CI will run stricter checks)

Acceptance:
- Pushing from clean repo passes without `--no-verify`
- When a real leak is introduced in tracked files, the hook blocks the push

Epic 1: Storage providers and artifact lifecycle (must-have, user-facing)
Scope:
- Make artifact download/archiving robust across Local and S3

Tasks:
- Server-side ZIP streaming for S3
  - Stream S3 objects into a ZIP to response without loading all in memory
  - Use small chunked GETs; keep memory < 64MB
- Preview endpoint for small files
  - GET `/api/v1/projects/{id}/files/{path}?preview=true` returns text/markdown/images with appropriate headers
  - Range support for S3 via `Range` and passthrough of partial responses
- Retention & cleanup
  - On project delete: delete provider files under project prefix (Local + S3)
- Storage health/capabilities (done initial):
  - Expand `/storage/capabilities` to include max preview size and archive support matrix

Tests:
- Integration tests for listing, direct download (local), presigned redirect (S3 mocked), server-side ZIP with 2–3 files
- Preview test for small text and markdown

Acceptance:
- ZIP archives downloadable for both providers (S3 streamed)
- Previews render small files reliably
- Delete cleans up artifacts

Epic 2: RBAC & Audit completeness (must-have, compliance)
Scope:
- Enforce permissions everywhere they matter and produce audit trails for critical actions

Tasks:
- RBAC
  - Replace remaining TODO admin checks (`analytics/system`, `monitoring.py`, `tenants.py` admin ops) with `require_permission(...)`
  - Seed role→permission mapping fixture for tests
- Audit events
  - Log pipeline start/restart/cancel; blueprint revision request; analytics export; tenant role changes
  - Include `user_id` (from token), request IP, user-agent if available
- Audit admin view endpoint
  - GET `/api/v1/audit?tenant_id=...&action=...&resource=...&limit&offset&time_range`

Tests:
- Permission denials across endpoints; audit log entries asserted for the above actions

Acceptance:
- Unauthorized calls return 403; happy-path writes audit records with expected fields

Epic 3: CI/CD and testing hardening (developer confidence)
Scope:
- Baseline CI that runs quickly and provides real signal

Tasks:
- GitHub Actions
  - Backend: setup Python + SQLite; run Alembic; run focused test suites (skip archived/legacy tests); enforce coverage threshold (line 65%)
  - Frontend: Jest unit tests; Playwright smoke (headless)
  - Upload artifacts on failure
- Repo-level hooks
  - Add `scripts/pre-push.sh` with repo-tuned checks and reference it in docs; keep global hook lenient
- Docs: README Quickstart (run backend tests, run frontend tests, storage config)

Acceptance:
- CI green on main; PRs show checks; a failing critical test blocks merge

Appendix – Current status snapshot
- Logs
  - DB write wired in `mvp_service._add_log` (async best-effort)
  - DB-first read with filters, search, sort, seek; summary endpoint in `pipelines.py`
  - Integration tests added for filters/seek/summary
- Storage
  - Provider abstraction in place; S3 presign for file download; local streaming; archive uses provider; capabilities endpoint added
- RBAC & Audit
  - `require_permission` fixed to be an async dependency; applied to key endpoints
  - Audit for file download, archive, blueprint approve; pipelines pause/resume

Work sequencing (strict)
1) Finish Epic 0 (pre-push sane defaults) – small changes, big win
2) Epic 1 (S3 ZIP + preview + cleanup)
3) Epic 2 (RBAC + audit breadth + admin audit list)
4) Epic 3 (CI baseline + docs)

Deliverables checklist (must turn green)
- [ ] Pre-push: tracked-only security scan; allowlist; VERSION file
- [ ] S3 server-side ZIP streaming
- [ ] Preview endpoint with range/size limits
- [ ] Artifact cleanup on delete
- [ ] RBAC completed in monitoring/tenants and TODOs removed
- [ ] Audit events added (start/restart/cancel/revise/export/role changes)
- [ ] Audit admin list endpoint
- [ ] GitHub Actions CI: backend + frontend + coverage + artifacts
