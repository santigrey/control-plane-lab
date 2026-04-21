# Project Ascension — Day 65
**Date:** Tue Apr 21 2026

## Completed this session
- **Google OAuth scope drift FIXED at root** (commit 281d382). Symptom: create_calendar_event returned HTTP 403 insufficient_scopes. Root cause: Day 64 reauth script only requested calendar.readonly, missing calendar.events. Real root cause was structural: scope list hardcoded in auth script, disconnected from the module making API calls.
- **Lock-in pattern deployed** (3 independent safety nets):
  1. Structural: SCOPES constant now lives INSIDE google_readers.py. reauth_gmail.py imports from google_readers.SCOPES via sibling import. Single source of truth.
  2. Runtime: new _assert_token_scopes() called inside _load_credentials(). Missing scope raises ScopeMismatchError with exact remediation command.
  3. Temporal: nightly smoke test exercises Google tools, triggering the assertion. Drift surfaces within 24h via Telegram alert.
- **Scope change**: calendar.readonly -> calendar.events (superset: read + write on events).
- **Branch recovery caught mid-flight**: initial commit landed on feat/persona-mode (working tree was parked there from earlier persona-mode shipping). Caught the '[feat/persona-mode 281d382]' output signal, fast-forward merged to main, pushed both branches.
- **Persona mode verified untouched**: zero file overlap between 281d382 and persona commits. Persona module intact, 'Hey Babe' trigger preserved.

## Verified end-to-end
- Token has calendar.events scope + refresh token
- Scope assertion passes on good token, fails loud on bad token with exact remediation URL
- Orchestrator restart clean, no ScopeMismatchError in boot log
- create_calendar_event: ok:true, Google event id 3h1f8i4i5l8056oj79tfap2e7s
- get_upcoming_calendar round-trip: new event appears in readback
- get_emails still returns 10 items
- Smoke test baseline unchanged: 15 PASS / 0 FAIL / 1 SCHEMA_ISSUE (get_system_status)

## Pending
- get_system_status schema cleanup (return {ok: True, ...} envelope)
- Dashboard /chat/private toggle (1-session P2 task)
- LinkedIn post: three-tier brain + optimization story
- Phase B: 70B QLoRA run
- Memory distillation nightly job
- Semantic router for automatic brain selection
- Tier 3 MQTT approval gate wiring
- Schlage lock integration
- Demo video for portfolio
- Smoke test unlisted tools: get_job_pipeline, plan_and_execute, read_course_material
