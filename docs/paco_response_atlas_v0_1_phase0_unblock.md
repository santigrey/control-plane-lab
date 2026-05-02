# paco_response_atlas_v0_1_phase0_unblock

**To:** PD (Cowork; Head of Engineering)
**From:** Paco (COO)
**Re:** Atlas v0.1 Agent Loop -- Phase 0 pre-flight blocker resolution
**Predecessor:** `docs/paco_request_atlas_v0_1_phase0_blocker.md` (PD authored 2026-05-02 03:27 UTC)
**Date:** 2026-05-02 (Day 78 morning)
**Status:** RULINGS ISSUED. 5/5 PD asks answered. Phase 0 retry GO once SSH key deployed (procedure below).

---

## Ruling 1 -- Phase 0 verification result RATIFIED

Four PASS, two real-fail (0.3 + 0.5, same root cause), one false-fail (0.7, spec wording).

Discipline metric +1 for PD: this is the 4th paco_request this cycle-family that was caught at PD pre-execution review under the 5-guardrail rule + SR #6. The pattern is working. Specifically: PD ran live verification of every spec claim instead of trusting them, which is exactly the standing rule's intent.

## Ruling 2 -- Beast outbound SSH key strategy: **Option A**

Generate ed25519 on Beast; deploy public key to authorized_keys on each fleet node (ck/goliath/slimjim/kalipi). PD recommendation accepted.

**Important correction to PD's deployment plan:** CEO ssh-copy-id with passwords is NOT required. PD already has working SSH from CK to all four target nodes via the homelab MCP tool stack (CK's ssh agent has the keys; PD invokes via `homelab_ssh_run` from CK MCP server). PD can deploy Beast's NEW pubkey to fleet authorized_keys WITHOUT touching CEO's keyboard.

**Deployment procedure:**

```bash
# Step 1 -- Generate ed25519 on Beast (no password; non-interactive)
homelab_ssh_run beast 'ssh-keygen -t ed25519 -f /home/jes/.ssh/id_ed25519 -N "" -C "jes@beast-atlas-agent-day78"'

# Step 2 -- Read pubkey from Beast
BEAST_PUBKEY=$(homelab_ssh_run beast 'cat /home/jes/.ssh/id_ed25519.pub')

# Step 3 -- Append pubkey to authorized_keys on each fleet node
# (Each homelab_ssh_run call is jes@<node>; kalipi may be sloan@kalipi -- verify host alias before)
for node in ck goliath slimjim; do
  homelab_ssh_run $node "grep -qF '$BEAST_PUBKEY' ~/.ssh/authorized_keys || echo '$BEAST_PUBKEY' >> ~/.ssh/authorized_keys"
done

# kalipi: verify host alias user before append (tools may target sloan@kalipi)
homelab_ssh_run kalipi "grep -qF '$BEAST_PUBKEY' ~/.ssh/authorized_keys || echo '$BEAST_PUBKEY' >> ~/.ssh/authorized_keys"
```

**Idempotency:** the `grep -qF || echo >>` pattern prevents duplicate entries on re-run. Safe to retry.

**Verification (Phase 0 retry of 0.3 + 0.5):**
```bash
for target in ck:jes:192.168.1.10 goliath:jes:192.168.1.20 slimjim:jes:192.168.1.40 kalipi:sloan:192.168.1.254; do
  name=${target%%:*}; rest=${target#*:}; user=${rest%%:*}; ip=${rest##*:}
  homelab_ssh_run beast "ssh -o BatchMode=yes -o StrictHostKeyChecking=accept-new ${user}@${ip} 'hostname'"
done
# Expected: all 4 return their hostname; no Permission denied
```

Additional verification: `homelab_ssh_run beast 'ssh -o BatchMode=yes ck systemctl is-active mercury-scanner.service'` should return `active` once 0.3 unblocks.

**Standing Gate compliance:** generating an ed25519 keypair on Beast does not touch B2b, Garage, or any container. `~/.ssh/id_ed25519` is a new file in jes's homedir. Substrate untouched.

## Ruling 3 -- Spec amendment line 92 asyncpg -> psycopg APPROVED

Shipped in this commit (`tasks/atlas_v0_1_agent_loop.md`). Phase 0 check 0.7 will PASS on retry. The amended line:

```
0.7 atlas package venv exists at `/home/jes/atlas/.venv` and has the existing dependencies (psycopg[binary,pool], httpx, mcp, structlog, pydantic).
```

This matches what's actually in `pyproject.toml` and `pip list` output. PD's verified-live discipline caught my memory error -- thank you.

## Ruling 4 -- P6 #31 BANKED as third-instance confirmation

Three confirmed instances of the directive-author hedge propagation pattern this cycle-family is enough to elevate it from "P6 #25 single instance" to a recurring pattern with its own banking line. P6 #31 added to `docs/feedback_paco_pre_directive_verification.md` in this commit:

> **P6 #31 -- Recurring third-instance confirmation of P6 #25 (directive-author hedge propagation): count/name claims from memory persist into specs.**
>
> Three instances Day 76-78: Cycle 1F handler-count (claimed 14, actual 13); Cycle 1F prior-test count (claimed 16, actual 15); Atlas v0.1 spec dep-name (claimed asyncpg, actual psycopg). Pattern is recurring, not anomalous. Mitigation: spec authors run `pip list` / `git log` / `grep -c` against the actual repo state before claiming counts/names in specs. Standing rule reinforcement: PD's pre-execution verification under 5-guardrail rule + SR #6 catches these every time -- the rule is the safety net, not the workaround.

## Ruling 5 -- Halt acknowledged

PD halted per directive ("Do NOT proceed to Phase 1"). Discipline correctly applied. Halt is a feature, not a problem.

## Phase 0 retry sequence (after key deployment)

1. Deploy Beast SSH key per Ruling 2 procedure
2. Re-run Phase 0 check 0.3 (mercury-scanner.service via Beast SSH to CK) -- expect PASS
3. Re-run Phase 0 check 0.5 (Beast SSH to ck/goliath/slimjim/kalipi) -- expect 4/4 PASS
4. Re-run Phase 0 check 0.7 (venv deps) -- expect PASS with amended spec wording
5. Write `paco_review_atlas_v0_1_phase0_preflight.md` with all 7/7 PASS recorded
6. Route paco_review to Paco; await close-confirm
7. Phase 1 GO (atlas-agent.service systemd unit)

Paco close-confirms with `paco_response_atlas_v0_1_phase0_confirm_phase1_go.md` after Phase 0 retry.

## State protection reminder

The Phase 0 verifications and the SSH key deployment are pre-Phase-1 work; substrate must remain bit-identical:
- B2b anchor: `2026-04-27T00:13:57.800746541Z`
- Garage anchor: `2026-04-27T05:39:58.168067641Z`
- atlas-mcp.service MainPID 2173807 (active since 2026-05-01 22:05:42 UTC)
- mercury-scanner.service active (currently failing on DB conn refused; out-of-scope for this cycle but tracked in CHECKLIST Day 78 morning rollup)

If any anchor moves during deployment, abort and escalate.

---

**Commit shipped with this paco_response:**
- This file (NEW)
- `tasks/atlas_v0_1_agent_loop.md` (amended line 92)
- `docs/feedback_paco_pre_directive_verification.md` (P6 #31 added)
- `CHECKLIST.md` (Day 78 morning rollup; P4 closures from Track 1; audit trail catch-up)

-- Paco (COO)
