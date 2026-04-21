# Project Ascension — Day 64
**Date:** Mon Apr 20 2026 (late / overnight)

## Completed this session
- **memory_save tool FIXED** (commit f1084a3) — wrong embed model (nomic-embed-text -> mxbai-embed-large) + wrong table (memories -> memory) + vec_str cast. Bug had silently failed for unknown duration. Auto-write path was unaffected.
- **Anti-hallucination prompt hardened** (commit 85f4ae1) — added TOOL FAILURE HONESTY clause. Forbids constructing infrastructure diagnoses from ambiguous tool errors. Behavioral test passed: induced read_file failure, Alexandra reported verbatim error + acknowledged uncertainty, did NOT fabricate.
- **Tool registry audit complete** (commit ef1b26e) — systematic smoke test of all 24 registered tools via direct handler invocation.

## Audit results (24 tools)
- PASS (10): ping, web_search, web_fetch, research_topic, get_linkedin_profile, get_live_context, home_status, list_files, read_file, memory_save
- FIXED TONIGHT (1): memory_recall — sister bug to memory_save, same two bugs + vec_str cast. Verified: recall query 'Day 64 memory_save fix' returned 3 results, top hit similarity 0.891. Memory layer now fully bidirectional.
- CREDENTIAL EXPIRED (3): get_emails, get_calendar, get_upcoming_calendar — shared Google OAuth token invalid_grant. MANUAL ACTION: Sloan must re-run OAuth flow. Not a code bug.
- SCHEMA CLEANUP (1): get_system_status returns None instead of dict — minor, not functional failure. Audit backlog.
- WORKING AS DESIGNED (9): home_cameras (Tier 3 approval gate), send_email/send_telegram/home_control/create_calendar_event/write_file (destructive tool validators all raising ValueError on missing args), job_search/job_search_jsearch/draft_message/sleep (audit script test inputs were wrong, tools are fine)
- UNLISTED (3): get_job_pipeline, plan_and_execute, read_course_material — not in my test set, untested

## Pending
- MANUAL: Re-run Google OAuth flow to restore get_emails / get_calendar / get_upcoming_calendar
- Dashboard /chat/private toggle (1 session of work)
- LinkedIn post: three-tier brain + iterative optimization story (ready to draft)
- Phase B: 70B QLoRA on same pipeline
- Memory distillation (nightly Goliath summarization)
- Semantic router for automatic brain selection
- Tier 3 MQTT approval gate wiring
- Schlage lock integration
- Demo video for portfolio
- get_system_status schema cleanup (minor)
- Smoke test 3 unlisted tools: get_job_pipeline, plan_and_execute, read_course_material

## Process notes / lessons captured
- Audit script false positive lesson: tools that depend on env vars look broken when tested outside orchestrator process (summarize appeared broken hitting 127.0.0.1, was actually fine in production). Future audits should either load .env or test via live HTTP to the running service.
- memory_save and memory_recall are sister functions with sister bugs. When fixing one, check the other.
- Anti-hallucination clause working: tool-failure behavioral test confirmed. Alexandra reports verbatim errors instead of fabricating diagnoses.
