# paco_review_atlas_v0_1_phase0_preflight

**Spec:** Atlas v0.1 Operations Agent Loop Build Spec (`tasks/atlas_v0_1_agent_loop.md`, commit `8195987` post amendment, 600 lines)
**Phase:** 0 -- Pre-flight verification (PD reads & verifies; no code)
**Status:** **7/7 PASS** post-retry. Phase 0 CLOSED. Ready for Phase 1 GO ratification.
**Predecessor:** `docs/paco_response_atlas_v0_1_phase0_unblock.md` (Paco rulings 1-5, HEAD `8195987`); `docs/paco_request_atlas_v0_1_phase0_blocker.md` (PD escalation, Day 78 morning)
**Author:** PD (Cortez session, 5th rule independent verification)
**Date:** 2026-05-02 UTC (Day 78 morning)
**Target host:** Beast (atlas operations agent runtime) + fleet (CK + Goliath + SlimJim + KaliPi)

---

## 0. Verified live (per 5th standing rule)

Independent live verification of every claim before recording PASS. All commands run via homelab_ssh_run from CK Cortez session.

| # | Claim | Verified by | Live result |
|---|---|---|---|
| 1 | atlas HEAD on /home/jes/atlas/ | `git log --oneline -3` on Beast | `d4f1a81 feat: Cycle 2B EVENTS_SOURCE_ALLOWLIST adds alexandra source for v0.2 Alexandra integration` (matches spec's `"d4f1a81 or later"`) |
| 2 | atlas-mcp.service active | `systemctl is-active` + `show -p MainPID -p ActiveEnterTimestamp` | `active`; MainPID 2173807; ActiveEnterTimestamp `Fri 2026-05-01 22:05:42 UTC` (~6h uptime through Phase 0 work) |
| 3 | mercury-scanner.service active via Beast->CK SSH | Beast SSH to CK (post key deployment) -> `systemctl is-active` | `active`; MainPID 4424; ActiveEnterTimestamp `Thu 2026-04-23 22:31:40 UTC` (~9 days continuous uptime) |
| 4 | Prometheus reachable from Beast | `curl http://192.168.1.40:9090/api/v1/query?query=up` | HTTP 200; 2.7ms; real metrics (`{"status":"success","data":{"resultType":"vector","result":[{"metric":{"__name__":"up","fleet":"santigrey","instance":"192.168.1.152:9100",...]`) |
| 5 | SSH Beast->ck/goliath/slimjim/kalipi key-auth | Beast SSH attempts with `-o BatchMode=yes` (no password prompt) | ck=sloan3 / goliath=sloan4 / slimjim=sloan1 / kalipi=kali-raspberrypi -- ALL 4 hostnames returned cleanly |
| 6 | Beast container anchors canonical | `docker inspect control-postgres-beast control-garage-beast` | postgres `2026-04-27T00:13:57.800746541Z`; garage `2026-04-27T05:39:58.168067641Z` -- bit-identical, holding 96+ hours |
| 7 | atlas .venv exists with deps (per amended spec) | `pip list` + `python -c 'import psycopg, psycopg_pool, httpx, mcp; from atlas.db import Database'` | venv exists; psycopg 3.3.3, psycopg-pool 3.3.0, httpx 0.28.1, mcp 1.27.0 (per `pip show`), structlog 25.5.0, pydantic 2.13.3 all installed; functional `from atlas.db import Database` clean |
| 8 | SSH key deployed per Paco Ruling 2 procedure | Beast `cat /home/jes/.ssh/id_ed25519.pub` + 4-node authorized_keys append | Beast pubkey: `ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIGmptnRq3B0IO15psjFsjxHdFdnIWASfnk2tvPwoBzgt jes@beast-atlas-agent-day78`; fingerprint `SHA256:bfDdPnhi0NesgfJS+FRsJDR7oeiO27aBUb+ycF4c0P4`; deployed (appended OK) to ck/goliath/slimjim/kalipi authorized_keys -- idempotent grep-guard pattern used (re-runs safe) |
| 9 | Standing Gates (substrate untouched) | docker inspect anchors + atlas-mcp.service status post-deployment | postgres+garage anchors bit-identical pre/post deployment; atlas-mcp MainPID 2173807 unchanged; Beast `/home/jes/.ssh/id_ed25519` is a NEW file in jes's homedir (no substrate impact) |
| 10 | mercury-scanner.service untouched | systemctl status via Beast->CK | active, MainPID 4424 unchanged from Day 67 era (Standing Gate #6 of build spec preserved) |
| 11 | Spec amendment line 92 (asyncpg -> psycopg) shipped | `grep psycopg tasks/atlas_v0_1_agent_loop.md` | shipped in commit `8195987`; reality matches now |
| 12 | P6 #31 banked | `grep "P6 #31" docs/feedback_paco_pre_directive_verification.md` | shipped in commit `8195987`; banking captures recurring third-instance pattern |

12 Verified-live items, 0 mismatches, 0 deferrals.

---

## 1. TL;DR

Phase 0 pre-flight verification CLOSED with **7/7 PASS** post-retry. Initial Phase 0 surfaced 3 of 7 checks failed (0.3 + 0.5 real blocker, 0.7 spec wording). Paco's 5 rulings (`docs/paco_response_atlas_v0_1_phase0_unblock.md`, HEAD `8195987`) resolved all 5 PD asks: (1) ratified PD verification, (2) approved Option A SSH key strategy with CK-MCP-mediated deployment (no CEO password entry needed), (3) approved spec amendment line 92 asyncpg->psycopg, (4) banked P6 #31 third-instance confirmation of P6 #25 pattern, (5) acknowledged halt.

Beast SSH key deployed via CK-MCP-mediated workflow: 1 key generation (Beast ed25519, fingerprint `SHA256:bfDdP...0P4`) + 4 idempotent appends to fleet authorized_keys + 4 verification SSHes from Beast (all returned hostnames cleanly).

Phase 0 retry verified all 7 checks pass:
- 0.1: atlas HEAD `d4f1a81` (Cycle 2B; exceeds spec "Cycle 1I or later")
- 0.2: atlas-mcp.service active (MainPID 2173807, ~6h uptime)
- 0.3: mercury-scanner.service active via Beast->CK SSH (MainPID 4424, ~9 days uptime)
- 0.4: Prometheus on SlimJim reachable from Beast (HTTP 200, 2.7ms)
- 0.5: SSH Beast->4 nodes (ck/goliath/slimjim/kalipi) all return hostnames cleanly
- 0.6: Beast anchors bit-identical (postgres + garage canonical values, 96+h holding)
- 0.7: atlas .venv + deps clean (psycopg/httpx/mcp/structlog/pydantic all importable + functional)

Substrate Standing Gates compliance: ALL 6 preserved through Phase 0 work (B2b publication / subscription untouched / Garage cluster untouched / mcp_server.py CK untouched / atlas-mcp.service untouched / nginx vhosts unchanged / mercury-scanner.service untouched).

Ready for Phase 1 GO (atlas-agent.service systemd unit).

---

## 2. Phase 0 retry sequence executed

### 2.1 Step A -- SSH key deployment per Paco Ruling 2 procedure

Generate Beast ed25519, read pubkey, deploy to 4 nodes via CK-mediated SSH (CK has working ssh keys to all targets; no CEO password entry needed).

```bash
# Step A.1 (Beast key generation)
ssh -i /home/jes/.ssh/id_ed25519 jes@192.168.1.152 'ssh-keygen -t ed25519 -f /home/jes/.ssh/id_ed25519 -N "" -C "jes@beast-atlas-agent-day78"'
# -> SHA256:bfDdPnhi0NesgfJS+FRsJDR7oeiO27aBUb+ycF4c0P4 jes@beast-atlas-agent-day78
# -> BEAST_KEY_GENERATED

# Step A.2 (read pubkey)
BEAST_PUBKEY=$(ssh -i /home/jes/.ssh/id_ed25519 jes@192.168.1.152 'cat /home/jes/.ssh/id_ed25519.pub')
# -> ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIGmptnRq3B0IO15psjFsjxHdFdnIWASfnk2tvPwoBzgt jes@beast-atlas-agent-day78

# Step A.3 (deploy to 4 nodes; idempotent grep-guard)
for entry in ck:jes@192.168.1.10 goliath:jes@192.168.1.20 slimjim:jes@192.168.1.40 kalipi:sloan@192.168.1.254; do
  name=${entry%%:*}; target=${entry#*:}
  ssh -i /home/jes/.ssh/id_ed25519 -o BatchMode=yes $target \
    "grep -qF '$BEAST_PUBKEY' ~/.ssh/authorized_keys && echo '  already present (idempotent skip)' || (echo '$BEAST_PUBKEY' >> ~/.ssh/authorized_keys && echo '  appended OK')"
done
# -> ck: appended OK
# -> goliath: appended OK
# -> slimjim: appended OK
# -> kalipi: appended OK

# Step A.4 (verify Beast can now SSH to all 4 nodes)
for entry in ck:jes@192.168.1.10 goliath:jes@192.168.1.20 slimjim:jes@192.168.1.40 kalipi:sloan@192.168.1.254; do
  name=${entry%%:*}; target=${entry#*:}
  ssh -i /home/jes/.ssh/id_ed25519 jes@192.168.1.152 "ssh -o BatchMode=yes -o StrictHostKeyChecking=accept-new $target hostname"
done
# -> ck: sloan3
# -> goliath: sloan4
# -> slimjim: sloan1
# -> kalipi: kali-raspberrypi
```

Idempotency note: re-running the deploy would skip via grep-guard. Future PD or CEO can re-run safely without authorized_keys duplication.

### 2.2 Step B -- Phase 0 retry verification (all 7 checks)

Full verbatim output captured. Summary:

| Check | Result | Evidence |
|---|---|---|
| 0.1 atlas HEAD | ✅ PASS | `d4f1a81 feat: Cycle 2B EVENTS_SOURCE_ALLOWLIST adds alexandra source for v0.2 Alexandra integration` |
| 0.2 atlas-mcp active | ✅ PASS | active, MainPID 2173807, ActiveEnterTimestamp `Fri 2026-05-01 22:05:42 UTC` |
| 0.3 mercury-scanner via Beast->CK | ✅ PASS | active, MainPID 4424, ActiveEnterTimestamp `Thu 2026-04-23 22:31:40 UTC` |
| 0.4 Prometheus from Beast | ✅ PASS | HTTP 200, 2.728ms, real metrics |
| 0.5 SSH Beast->4 nodes | ✅ PASS ALL 4 | ck=sloan3, goliath=sloan4, slimjim=sloan1, kalipi=kali-raspberrypi |
| 0.6 Beast anchors | ✅ PASS | postgres `2026-04-27T00:13:57.800746541Z`, garage `2026-04-27T05:39:58.168067641Z` bit-identical |
| 0.7 atlas .venv deps (amended) | ✅ PASS | psycopg 3.3.3, psycopg-pool 3.3.0, httpx 0.28.1; functional `from atlas.db import Database` clean |

0.7 minor wrinkle: `mcp.__version__` raised AttributeError because the mcp module doesn't expose `__version__` (probe-style mismatch); `pip show mcp` confirms 1.27.0 installed; `import mcp` works. Spec PURPOSE satisfied (deps installed and functional).

---

## 3. Standing Gates compliance (per build spec section "Standing Gates")

| # | Gate | Pre-Phase-0 | Post-Phase-0 |
|---|---|---|---|
| 1 | B2b publication / subscription untouched | postgres anchor `2026-04-27T00:13:57.800746541Z` | bit-identical |
| 2 | Garage cluster untouched | garage anchor `2026-04-27T05:39:58.168067641Z` | bit-identical |
| 3 | mcp_server.py on CiscoKid untouched | (untouched throughout cycle) | unchanged |
| 4 | atlas-mcp.service untouched (loopback :8001 preserved) | MainPID 2173807, active since 2026-05-01 22:05:42 UTC | unchanged |
| 5 | nginx vhosts on CiscoKid unchanged | (untouched throughout cycle) | unchanged |
| 6 | mercury-scanner.service on CK untouched | MainPID 4424, active since 2026-04-23 22:31:40 UTC | unchanged |

6/6 Standing Gates preserved through Phase 0 work.

The SSH key generation on Beast added a new file (`/home/jes/.ssh/id_ed25519` + `.pub`) in jes's homedir. This is application-layer state (jes's user-level SSH config), NOT substrate. No container, no daemon, no service touched. Authorized_keys appends on the 4 fleet nodes are also application-layer (user-level SSH config), not substrate.

---

## 4. State at Phase 0 close

- atlas HEAD: `d4f1a81` (Cycle 2B unchanged from cycle entry; expected since Phase 0 is verification-only)
- atlas-mcp.service: active, MainPID 2173807, ~6h uptime
- mercury-scanner.service: active, MainPID 4424, ~9 days uptime
- Beast SSH outbound capability: NEW (ed25519 fingerprint `SHA256:bfDdP...0P4`); deployed to 4 fleet nodes' authorized_keys
- Prometheus on SlimJim: reachable from Beast for Domain 1 queries
- B2b + Garage anchors: bit-identical, 96+h holding
- HEAD on control-plane-lab: `8195987` (Phase 0 unblock + spec amendment + P6 #31 + Day 78 CHECKLIST rollup)
- atlas package venv: clean with all 6 dependencies + dev tools functional

---

## 5. Asks of Paco

1. **Confirm Phase 0 7/7 PASS** against the captured verified-live evidence (sections 0 + 2).
2. **Confirm Standing Gates 6/6 preserved** (section 3).
3. **Authorize Phase 1 GO** -- atlas-agent.service systemd unit per build spec section "Phase 1" (lines 99-138).
4. **Acknowledge SSH key deployment** as application-layer (user-level SSH config), NOT substrate per Standing Gate #4 wording ("atlas-mcp.service untouched (loopback :8001 bind preserved; this cycle ADDS atlas-agent.service alongside)").

---

## 6. Cross-references

**Doc trail:**
- `tasks/atlas_v0_1_agent_loop.md` (build spec, commit `8195987` post amendment)
- `docs/paco_request_atlas_v0_1_agent_loop_picks.md` (8 ratified picks)
- `docs/paco_request_atlas_v0_1_phase0_blocker.md` (PD escalation Day 78 morning)
- `docs/paco_response_atlas_v0_1_phase0_unblock.md` (5 rulings, HEAD `8195987`)
- `docs/feedback_paco_pre_directive_verification.md` (P6 #31 banked, HEAD `8195987`)

**Discipline metrics this cycle:**
- 4 paco_requests caught at PD pre-execution review under 5-guardrail rule + SR #6 (handler count / pretest flake / args-wrapping / Phase 0 SSH key+dep name)
- 3 of 4 are P6 #25/#31 family (recurring directive-author hedge propagation)
- 5th rule reinforced: PD's verified-live discipline catches every memory-vs-reality mismatch before Phase work begins

---

## 7. Status

**AWAITING PACO CLOSE-CONFIRM + PHASE 1 GO.**

PD paused. Beast SSH key live and verified to all 4 fleet nodes. Phase 1 atlas-agent.service systemd unit is the next deliverable per Paco Ruling 2 sequence step 7.

-- PD
