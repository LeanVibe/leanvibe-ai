# Next 4 Epics Plan

## Epic 1: Pipeline Monitoring & Control (Pause/Resume, Logs)
- Goal: Real-time, controllable pipeline execution with detailed logs.
- Deliverables:
  - Pause/resume endpoints functional, reflected in project status.
  - In-memory execution logs with level, message, stage, timestamp.
  - WebSocket-safe orchestration that halts between agent stages while paused.
- Tasks:
  - Backend
    - Orchestrator: add paused state per project; check-and-wait before each agent execution; expose `pause_generation` and `resume_generation`.
    - MVP Service: add `pause_mvp_generation`, `resume_mvp_generation`; add in-memory log store and `add_log`, `get_generation_logs`.
    - Pipelines API: wire `/pause`, `/resume` to MVP Service; update `/logs` to read from service and support filters.
    - Emit basic logs at stage transitions and retries.
  - Frontend
    - Hook: ensure `useWebSocket` supports pipeline updates (already set); add handlers for new events if added later.
    - UI: add controls (Pause/Resume) and a simple logs panel (follow-up task).
  - Tests
    - Unit: orchestration pause/resume flows.
    - API: pause/resume endpoints happy-path and error cases.
    - E2E (follow-up): Playwright pipeline controls.
- Acceptance Criteria:
  - Pausing during generation sets status to `paused` and stops progression to next agent until resumed.
  - Resuming continues from the next checkpoint without losing recorded progress.
  - `/logs` returns recent logs; filters work.

## Epic 2: Project Files & Artifact Browser
- Goal: Browse, preview, and download generated artifacts.
- Deliverables:
  - Storage abstraction (local/S3) with signed URLs support.
  - Endpoints: list files, download file, download archive.
  - Frontend file browser with previews (text, md, image, logs).
- Tasks:
  - Backend: implement storage service, replace TODOs in `mvp_projects.py`.
  - Frontend: file browser UI, preview panes, search, type icons.
  - Security: tenant scoping, audit logs.
- Acceptance:
  - Users can browse artifacts, preview inline, and download with correct headers and permissions.

## Epic 3: Founder Interview Wizard & Onboarding
- Goal: Structured multi-step intake that seeds AI pipeline.
- Deliverables:
  - Multi-step wizard (Zod + RHF) with autosave and resume.
  - Backend interview persistence and endpoints; link to MVP project creation.
- Tasks:
  - Backend: interview models/ORM, CRUD endpoints, link into pipeline creation.
  - Frontend: wizard UI, validation, autosave, resume.
  - Tests: API and Playwright flow from signup to dashboard.
- Acceptance:
  - New founder completes wizard, submission creates project/pipeline, redirect to dashboard.

## Epic 4: End-to-End Testing & Quality Gates
- Goal: Production-grade test rigor and CI gates.
- Deliverables:
  - Jest unit coverage targets; Playwright auth+dashboard flows.
  - Backend contract and integration tests; perf smoke.
  - CI with coverage thresholds and artifact uploads.
- Tasks:
  - Frontend: expand unit tests; add Playwright.
  - Backend: increase coverage on orchestration and APIs; OpenAPI contract checks.
  - CI: parallel test matrix, coverage gates; log redaction checks.
- Acceptance:
  - CI fails on coverage regressions; E2E suite green on local and staging; API breaking changes detected.

## Sequencing
1. Epic 1 and 2 in parallel (shared API surface). Start with pause/resume + logs, then storage.
2. Epic 3 after foundational APIs are stable.
3. Epic 4 runs throughout, tightening gates near release.
