# Santigrey Standing Rules

**Owner:** Paco (COO) enforce, PD (Head of Engineering) honor.
**Source of truth:** This file. Rules accrete here as they emerge. Each rule has an origin (which task or incident surfaced it).
**Status:** RATIFIED 2026-04-26 (Day 72) by CEO. Effective immediately.
**Last updated:** 2026-04-26 (Day 72) -- Rule 1 ratified
**Mirror:** iCloud `/AI/Santigrey/STANDING_RULES.md`

---

## Rule 1 — MCP fabric is for control, not bulk data

**Origin:** P2 item A. Surfaced Day 70 PM during MCP fabric diagnosis (control plane only, no data plane). Ratified into the data-plane sequence as a standing principle alongside D2/D3/D4 capability work.

### What goes through MCP

- Single shell commands and their output (`homelab_ssh_run`)
- Single file reads up to ~1MB (`homelab_file_read`)
- Single file writes up to 5MB (`homelab_file_write`, post-D2)
- File transfers under ~10MB (planned: `homelab_file_transfer`, D3)
- Status queries, signaling, agent-to-agent messages, task pipeline events

### What does NOT go through MCP

- **Bulk file syncs** between hosts → use `rsync -av` over SSH
- **Database replication** → use Postgres logical replication (planned: B2)
- **Object storage** (logs, scrapes, artifacts, snapshots) → use S3-compatible API direct to MinIO (planned: B1)
- **Container image transfers** → use registry pulls
- **Backups** → use restic, rclone, or pg_dump piped over SSH
- **Streaming large outputs** → tail to a file on the target, then read the file via MCP if needed; or use journalctl over SSH

### Why

1. **Three serialization boundaries.** MCP carries JSON over streamable-HTTP through nginx through Python. Every byte hits each boundary. Bulk through MCP is wasted CPU and wasted clarity.
2. **False bottlenecks.** Routing bulk through MCP makes the control plane look like the data plane, which makes capacity planning meaningless and fault diagnosis ambiguous.
3. **Fail-fast is the goal.** The control plane should refuse bulk attempts loudly, not silently degrade. This rule makes that explicit.

### Operational expectations

- **Spec drafting (Paco):** Any task that would move >10MB of data between hosts MUST specify the transport (rsync, scp, S3 PUT, registry push, etc.). The spec MUST NOT route bulk through MCP tools by default.
- **Spec drafting (Paco):** Any tool call that would routinely return >1MB of output MUST route the output to a file on the target host. MCP carries the path or handle, not the bytes.
- **Execution (PD):** When implementing a spec, if PD finds a step that would push bulk through MCP, PD flags the issue back to Paco rather than silently routing through MCP.
- **Review (CEO):** Audit-trail entries for any rule violation. Reinforcement, not punishment.

### How violations surface

- Caught at spec drafting → revise the spec before PD sees it.
- Caught at execution → PD flag → Paco revise → re-issue.
- Caught in retrospective → audit-trail entry + a P6 methodology refinement so it doesn't recur.

---

## Future rules (placeholder)

More rules will land here as P6 methodology items get codified. Candidate next entries:

- Spec template requirements (restart safety, health-check semantics, PD report deliverable, bundled-verification deferred-restart) — currently three open P6 items, will consolidate into Rule 2 once codified.
- No claim about state without source verification first — currently P6 item, will become Rule 3.
- Verify-what-depends-on-a-credential — currently P5 carryover from Day 69, will become Rule 4 once doc is drafted.

---

## How this doc is used

- Paco reads this at session open alongside CHECKLIST.md.
- Each new rule lands with: title, origin (task/incident), what counts as in/out of scope, why, operational expectations, violation handling.
- Rules are versioned by edit history in git; no version stamps inside the file.
- This doc is canon, not a draft. If a rule is unclear or wrong, raise it as a CHECKLIST item, fix it via commit, don't shadow it with another file.
