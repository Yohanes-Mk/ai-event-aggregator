# Demo Phases Checklist

This file tracks the demo-first roadmap so another coding agent can continue from the current state without reconstructing the plan from chat history.

> **Convention:** Update this file whenever demo/UI work advances.
> Mark checklist items as done only when the code is shipped in this repo.
> Add short dated notes under the relevant phase when scope changes, tradeoffs are decided, or implementation is partially complete.

---

## Phase 0 — Demo Constraints and Prerequisites

- [x] Pick a demo-first shell that matches the current Python stack
- [x] Reuse existing DB/services instead of building a parallel demo backend
- [x] Add the demo dependency needed to run the app locally
- [x] Add a demo-specific env/readiness checklist to docs if setup friction appears

### Notes
- 2026-03-12: Chosen shell is Streamlit, not Vercel/Next, because the goal is a fast local demo over the existing Python pipeline.
- 2026-03-12: `streamlit` was added as a project dependency and verified via import.
- 2026-03-12: The demo app now loads `.env` at startup and shows env readiness in the UI so email failures are easier to diagnose.
- 2026-03-12: Added `.streamlit/config.toml` so the demo shell uses a project-local Streamlit theme instead of raw defaults.

## Phase 1 — Streamlit Operator Shell

- [x] Create `scripts/demo_app.py`
- [x] Show real DB metrics for videos, events, digests, and curator runs
- [x] Show latest ranked videos from the latest curator run
- [x] Show upcoming events from the DB
- [x] Add clear empty states when data is missing

### Notes
- 2026-03-12: The demo app now reads the live DB and shows metrics, top ranked videos, upcoming events, and recent digests without rebuilding business logic in the UI layer.
- 2026-03-12: The layout was reworked so the dashboard preview comes first, demo actions come second, and the DB-backed supporting data is lower on the page.
- 2026-03-12: The visual direction shifted toward Streamlit-native containers, tabs, metrics, pills, and sidebar sections instead of relying on a single heavy custom HTML skin.

## Phase 2 — On-Demand Actions

- [x] Add "Render Dashboard" action using existing dashboard service
- [x] Add "Send YouTube Digest" action using existing email service
- [x] Add "Send Events Digest" action using existing email service
- [x] Allow recipient override from the demo UI
- [x] Surface success/failure feedback in the app

### Notes
- 2026-03-12: The existing email services now support recipient override and return success booleans so the demo app can report real action outcomes instead of guessing.
- 2026-03-12: The UI now exposes env-readiness state before send actions so Gmail/OpenAI misconfiguration is visible without digging into code.

## Phase 3 — Dashboard Preview

- [x] Show generated dashboard artifact path
- [x] Add inline preview of the generated HTML
- [x] Add refresh action so the preview updates after render

### Notes
- 2026-03-12: The preview reads `artifacts/dashboard.html` directly and reuses the same generated artifact path as the main pipeline.
- 2026-03-12: The preview was moved to the top of the page because it is the strongest demo artifact and should be shown before the operator controls.

## Phase 4 — Demo-Friendly Personalization

- [x] Add visible profile context section for demo narration
- [ ] Allow temporary profile override for ranking if the underlying agent path supports it cleanly
- [ ] Avoid fake personalization UI that is not actually wired into ranking logic

### Notes
- 2026-03-12: Current curator logic still uses the existing repo user context flow, so profile editing should not be faked in the UI until the underlying path is real.
- 2026-03-12: Added a text-based context editor in the demo app that writes directly to `docs/user_context.md`, which matches the repo's real source-of-truth model better than a fake structured profile form.
- 2026-03-12: The curator now reads `docs/user_context.md` at runtime instead of import time, so context edits can affect future ranking runs without restarting the app.
- 2026-03-12: Added timestamped context snapshot support under `docs/context_snapshots/` plus a demo-app archive button so the current profile can be preserved before edits.

## Phase 5 — Channel Customization

- [x] Display currently tracked YouTube channels
- [x] Add a safe demo-only explanation for how channels are changed today
- [ ] Only add in-app channel editing when it can be done without creating config drift

### Notes
- 2026-03-12: The demo app now shows the configured channel list and explicitly tells the operator that channel changes are still code-driven rather than pretending there is persistent in-app editing.
- 2026-03-12: The channel list is now presented as pills in the sidebar, which reads better visually than a long markdown bullet list.

## Phase 6 — Demo Readiness and Operator Flow

- [x] Add `make demo`
- [x] Verify the Streamlit app imports and starts cleanly
- [ ] Verify the demo app can trigger real dashboard rendering
- [x] Verify the demo app can trigger real email delivery
- [x] Add a short demo-day runbook if needed

### Notes
- 2026-03-12: `make demo` now launches `streamlit run scripts/demo_app.py`. Import verification passed; dashboard generation was also exercised through the same service path the UI uses.
- 2026-03-12: Bare import verification still passes after the layout rebuild and `.env` loading change.
- 2026-03-12: Email delivery from the demo app was user-verified after the `.env` loading fix.
- 2026-03-20: Added a Streamlit Community Cloud deploy runbook to `README.md`, a `.streamlit/secrets.toml.example` template, and startup-side DB bootstrap so a fresh hosted Postgres can come online without a separate manual init step.
- 2026-03-20: The demo app now shows a setup screen when DB config/bootstrap fails instead of crashing immediately, which makes hosted deployment issues much easier to diagnose.

## Phase 7 — Post-Demo Evolution

- [ ] Decide whether the Streamlit app remains an internal operator console or is replaced later
- [ ] Reuse the same data/query/service path in future API/dashboard work
- [ ] Keep demo-only code thin so it does not become the product by accident

---

## Next Recommended Build Order

1. Streamlit shell with real DB metrics and ranked/event sections
2. On-demand dashboard and email actions
3. Inline dashboard preview
4. `make demo` and local verification
