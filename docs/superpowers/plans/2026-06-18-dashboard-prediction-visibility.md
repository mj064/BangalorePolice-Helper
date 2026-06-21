# Dashboard Prediction Visibility Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add next-day prediction visibility to the existing dashboard without breaking the current hotspot workflow.

**Architecture:** Extend the dashboard orchestration layer to fetch predictions alongside current hotspot data, add dedicated prediction KPI and list components in the left rail, and reuse the existing details panel by adding optional prediction context. Keep the map and hotspot APIs unchanged.

**Tech Stack:** React, TypeScript, Vite, Tailwind, Axios, Recharts

---

### Task 1: Add prediction API typing and dashboard state plumbing

**Files:**
- Modify: `frontend/src/services/api.ts`
- Modify: `frontend/src/pages/DashboardPage.tsx`

- [ ] Add typed prediction response support in `frontend/src/services/api.ts`.
- [ ] Add prediction loading/state handling in `frontend/src/pages/DashboardPage.tsx`.
- [ ] Add hotspot-to-prediction matching logic without changing hotspot fetching behavior.

### Task 2: Add prediction KPI and list UI

**Files:**
- Create: `frontend/src/components/PredictionKPIStats.tsx`
- Create: `frontend/src/components/PredictionsList.tsx`
- Create: `frontend/src/utils/risk.ts`
- Modify: `frontend/src/pages/DashboardPage.tsx`

- [ ] Add reusable risk-level color helpers in `frontend/src/utils/risk.ts`.
- [ ] Add a compact prediction KPI strip showing highest risk, predicted high-risk count, and average risk.
- [ ] Add a “Tomorrow’s High-Risk Zones” list with clickable rows and risk-level styling.

### Task 3: Extend the details panel for prediction context

**Files:**
- Modify: `frontend/src/components/HotspotDetailsPanel.tsx`
- Modify: `frontend/src/pages/DashboardPage.tsx`

- [ ] Add optional prediction props to the details panel.
- [ ] Show tomorrow risk score, prediction horizon, and trend comparison when a prediction is selected.
- [ ] Preserve existing hotspot detail fetching and charts when a matched hotspot exists.

### Task 4: Verify and document

**Files:**
- Modify: `docs/AGENT_PROGRESS.md`
- Modify: `docs/HANDOFF.md`

- [ ] Run `cd frontend && npm run build`.
- [ ] Run the local frontend and verify the new prediction UI manually.
- [ ] Update the handoff/progress docs with the new dashboard prediction capability and any remaining gaps.
