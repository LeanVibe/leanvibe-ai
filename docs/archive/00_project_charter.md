# 00_project_charter.md

## 1. Vision

To empower passionate senior engineers to finalize their dream side projects with a semi-autonomous L3 coding agent that runs on their own hardware and can be easily controlled from their iOS device.

## 2. Core Principles

*   **Local-First & Privacy-First**: All processing, including AI model inference, runs entirely on the user's local hardware. No code or data is ever sent to the cloud.
*   **Human-in-the-Loop**: The agent is semi-autonomous. It operates with confidence scores and quality gates, requiring human approval for actions where confidence is low. The user always has the final say.
*   **Seamless Workflow Integration**: The system is designed to integrate deeply into a senior developer's existing workflow (e.g., terminal-first with `vim`+`tmux`) while being complemented by a seamless iOS monitoring app.

## 3. Key Features & Value Proposition

*   **Live Dependency Mapping**: The agent analyzes code in real-time to provide an always-up-to-date visualization of the project's architecture, helping to prevent architectural drift.
*   **Automated Change Impact Analysis**: By understanding the codebase as a graph, the agent can identify and alert the developer to the potential impact of any changes before they are committed.
*   **Unified Interface (CLI + iOS)**: A powerful, terminal-first CLI is the primary interaction point, while a rich iOS app provides at-a-glance monitoring, visualization, and control.

## 4. Definition of Done (DoD)

A feature is considered "done" only when it meets the following criteria:
*   The implementation is covered by a comprehensive suite of automated tests (unit, integration).
*   The code adheres to the style and quality guidelines defined in `AGENTS.md`.
*   It is fully integrated into the vertical slice (Backend, CLI, and iOS if applicable).
*   Any new commands or workflows are documented.
*   The feature directly serves a core user journey as defined in this charter. 