# GAMMA Agent - Task 03: iOS Metrics & Monitoring Dashboard

**PRIORITY: HIGH**
**STATUS: COMPLETE**

## 1. Context & Objective

With the Architecture Viewer complete and the Kanban API integration underway, your next assignment is to build the **Metrics & Monitoring Dashboard** for the iOS app, as detailed in **Phase 6** of the `MOBILE_APP_ENHANCEMENT_PLAN.md`.

This dashboard will provide users with real-time insights into the AI's performance, confidence, and decision-making processes.

The backend APIs for this feature should have been implemented by Agent Beta in the `feature/ios-support-apis` branch. Your primary focus is on the iOS frontend implementation.

## 2. Worktree & Branch

-   **Worktree**: `../leenvibe-ios-dashboard`
-   **Branch**: Create a new branch `feature/ios-metrics-dashboard` from `sprint-1-foundation`.

**Action**: All work for this task must be committed to this new branch within the dashboard worktree.

## 3. Technical Specifications

### 3.1. UI Components

You will create a new view, accessible from the main `TabView`, that contains two primary sections:

**1. Metrics Visualization View:**
    -   Use the `Charts` framework in SwiftUI.
    -   Display a line chart showing **"Confidence Score Over Time"**.
    -   Display a bar chart showing **"Task Completion Rate"** (by status: Done vs. Others).
    -   Include a summary view for key stats like "Average Confidence" and "Total Tasks Completed".

**2. Decision Log View:**
    -   Create a scrollable `List` that displays the AI's decision history.
    -   Each row should show the decision, the reason, the confidence score, and a timestamp.
    -   Implement a search or filter bar to find specific decisions.

### 3.2. Backend Integration

-   You will need to create a new `MetricsService` in the iOS app to fetch data from the backend.
-   Connect to the following endpoints (implemented by Beta):
    -   `GET /metrics/{client_id}/history` to populate the charts.
    -   `GET /decisions/{client_id}` to populate the decision log.
-   Handle loading states, empty states (for new projects), and potential API errors gracefully in the UI.

### 3.3. File Structure

Create the following new files within the `LeenVibe-iOS` project:

```
LeenVibe-iOS/LeenVibe/
├── Views/
│   ├── Metrics/
│   │   ├── MetricsDashboardView.swift   # Main container view
│   │   ├── ConfidenceChartView.swift
│   │   ├── TaskRateChartView.swift
│   │   └── DecisionLogView.swift
├── ViewModels/
│   └── MetricsViewModel.swift         # Logic for fetching and preparing data
└── Services/
    └── MetricsService.swift           # Networking logic for metrics endpoints
```

## 4. Testing Requirements

-   Create new unit tests for the `MetricsViewModel` to verify data transformation logic.
-   Create new UI tests to ensure the charts and lists render correctly with mock data.
-   If you encounter issues with the backend APIs, **do not attempt to fix them**. Document the issue (the endpoint, the request, and the unexpected response) and flag it immediately by creating a `NEEDS_BACKEND_FIX.md` file in the root of the worktree.

## 5. Definition of Done

This task is complete when:
-   [ ] A new "Metrics" tab is added to the main `TabView`.
-   [ ] The `MetricsDashboardView` correctly displays the confidence and task rate charts.
-   [ ] The `DecisionLogView` correctly displays a filterable list of AI decisions.
-   [ ] The frontend successfully fetches and displays data from the backend metrics APIs.
-   [ ] The UI includes proper loading, empty, and error states.
-   [ ] All new code is committed to the `feature/ios-metrics-dashboard` branch in the `../leenvibe-ios-dashboard` worktree.

This task is critical for providing users with transparency into the AI's operations and delivering on a core promise of the MVP. 