# Active Context: LeenVibe

## 1. Current Sprint: 2.3 - Real-time Terminal Notifications

The primary objective of this sprint is to transform the CLI into a live, reactive monitoring and notification system.

### Key Deliverables:
*   **Background Notification Service**: Implement a non-blocking service to provide real-time terminal notifications that don't interrupt active commands.
*   **Desktop Notifications**: Integrate cross-platform desktop notifications for critical events like architectural violations or build failures.
*   **Live Dashboard**: Enhance the `monitor` command to act as a live metrics dashboard with notification overlays.
*   **Notification Management**: Implement features for viewing notification history and configuring notification preferences.

## 2. Recent Cleanup (January 2025)

**Technical Debt Addressed**:
- ✅ Created comprehensive `.gitignore` to prevent cache/build files from being tracked
- ✅ Moved integration tests from root to proper `tests/integration/` directory
- ✅ Consolidated iOS implementations - kept `LeenVibe-iOS` (with QR scanner) as canonical
- ✅ Archived older iOS implementations (`LeenVibe-iOS` and `LeenVibe-SwiftPM`) to `docs/archive/ios-implementations/`
- ✅ Moved single-use scripts to `docs/archive/single-use-scripts/`
- ✅ Cleaned up duplicate directories and cache files
- ✅ Removed outdated `requirements.txt` (project uses `pyproject.toml` with `uv`)

## 3. Upcoming Sprints Overview

- **Sprint 2.4**: Create simple YAML configuration management.
- **Sprint 2.5**: Add project-aware CLI integration.
- **Sprint 3**: iOS companion app with visualization.
- **Sprint 4**: Performance optimization and scaling.
- **Sprint 5**: Advanced AI features and intelligence.
- **Sprint 6**: Production readiness and security.

*This roadmap is based on the master plan, now archived in `docs/archive/PLAN.md`.*