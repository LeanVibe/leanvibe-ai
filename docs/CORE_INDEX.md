## Core documentation index

Use this as the single entry point for LeanVibe documentation. Each document has a clear scope to reduce duplication and drift.

### Essentials
- README.md — Top-level overview and quick start
- ARCHITECTURE.md — System architecture and design principles
- DEVELOPMENT_GUIDE.md — Developer onboarding and daily workflow
- CONFIGURATION.md — Environment variables and configuration per env
- TESTING_GUIDE.md — 4-tier testing strategy and practices
- DEPLOYMENT_GUIDE.md — CI/CD, deployment, rollback, and operations hand-off
- SECURITY.md — Security policy and best practices
 - docs/PORTS.md — Canonical port assignments (backend 8765, vector store 8001)

### Operations and monitoring
- OPERATIONS_PLAYBOOK.md — Daily ops, incident response, runbooks
- MONITORING.md — Observability architecture and probe system

### User-facing
- USER_GUIDE.md — End-user getting-started and common tasks
- GLOSSARY.md — Terminology and navigation hints

### Status and roadmaps
- docs/core/PRODUCTION_STATUS.md — Production readiness and KPIs
- docs/organized/production/PRODUCTION_READINESS_REPORT.md — Detailed readiness report
- docs/archive/plans/DEPRECATION_PLAN.md — Deprecations and migration plan (historical)

### Historical and specialized docs
- docs/organized/** — Curated, topic-specific deep dives
- docs/archive/** — Historical plans, reports, and deprecated specs

### Indexes and navigation
- docs/INDEX.md — Human-readable repository index
- docs/repo_index.json — Machine-readable repository map (for CLI agents)

Notes
- Prefer linking to this index from other docs to keep navigation consistent.
- When updating any of the core docs above, also update this index if scope materially changes.
