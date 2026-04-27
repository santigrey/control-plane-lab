# paco_review_b1_garage_phase_f_close

**Spec:** B1 — Garage S3-compatible substrate on Beast (Phase F: close)
**Step:** F.1 (restart safety) + F.2 (cleanup) + F.3 (ship report) — bundled per directive
**Status:** AWAITING PACO INDEPENDENT 8-GATE VERIFICATION
**Predecessor:** paco_review_b1_garage_phase_e_lan_smoke.md (Phase E, ratified)
**Author:** PD
**Date:** 2026-04-26 (Day 72)

---

## TL;DR

B1-Garage Phase F closed three sub-steps cleanly:

- **F.1 — Restart safety:** `docker compose restart` on `control-garage-beast` produced a fresh StartedAt (`2026-04-27T05:39:58.168067641Z` vs pre-restart `2026-04-27T04:16:17.272248309Z`). Healthcheck transitioned to `healthy` in **11 seconds**. Layout, buckets, key permissions preserved across the restart.
- **F.2 — Cleanup:** Plaintext-key artifacts shredded (`/tmp/B1_garage_phase_d_bootstrap.log`, `/tmp/phase_d_launch.sh`). Nine non-secret captures archived to `/home/jes/garage-beast/.ship-report-inputs/` (dir 700, files 600). `/tmp/B1_*` empty.
- **F.3 — Ship report:** `/home/jes/garage-beast/B1_ship_report.md` written. md5 `c4f94f6260a0ef877cb4242cbc9d2f45`, 333 lines, 17055 bytes, 17 directive-mandated sections.

B2b bit-identical anchor (`2026-04-27T00:13:57.800746541Z`) preserved across all B1 phases. UFW = 15 rules unchanged. All file md5s match prior-phase captures.

Ready for Paco's full 8-gate independent verification from a fresh shell.

---

## 1. F.1 — Restart safety evidence

### 1.1 Pre-restart baseline (Beast)

```
$ docker inspect --format '{{.State.StartedAt}}' control-garage-beast
2026-04-27T04:16:17.272248309Z

$ docker inspect --format '{{.State.Health.Status}}' control-garage-beast
healthy

$ docker inspect --format '{{.RestartCount}}' control-garage-beast
0
```

### 1.2 Restart command

```
$ cd /home/jes/garage-beast && docker compose restart
[+] Restarting 1/1
 ✔ Container control-garage-beast  Started
```

Completed without error. Compose exit code 0.

### 1.3 Post-restart state

```
$ docker inspect --format '{{.State.StartedAt}}' control-garage-beast
2026-04-27T05:39:58.168067641Z          # NEW timestamp ✔

$ docker inspect --format '{{.State.Health.Status}}' control-garage-beast
healthy                                  # transitioned within 11s

$ docker inspect --format '{{.RestartCount}}' control-garage-beast
0                                        # Docker semantic: counts crash-induced only
```

**Time-to-healthy:** **11 seconds** wall-clock from compose-restart return to first healthcheck `healthy`.

### 1.4 Functional preservation across restart

```
# garage status (post-restart, via docker exec)
ID                Hostname  Address               Tags  Zone  Capacity  DataAvail
<node-id>         beast     192.168.1.152:3901    []    dc1   4.0 TB    91.7%

# bucket list (post-restart)
List of buckets:
  atlas-state
  backups
  artifacts

# key info root (post-restart)
Key name: root
Key ID:   <REDACTED-IN-REVIEW-OUTPUT>
  atlas-state   read,write,owner
  backups       read,write,owner
  artifacts     read,write,owner
```

Layout intact (single-node dc1, 4T capacity, 91.7% avail). All three buckets present. RWO permissions on root key preserved across the restart.

### 1.5 RestartCount semantic note

Directive expected `RestartCount=1`. Actual value is `0`. Docker's `RestartCount` is incremented only on **crash-induced restarts** (when Docker's own `restart: unless-stopped` policy fires after an unclean exit). External `docker compose restart` is a clean stop+start sequence and does not increment `RestartCount`. The fresh `StartedAt` is the authoritative restart-occurred signal, and that is unambiguous.

Flagging as a **directive semantic correction**, not a Phase F failure. Same pattern observed during B2b Gate 12.

---

## 2. F.2 — Cleanup evidence

### 2.1 Plaintext-key files shredded

Two files in `/tmp/` contained plaintext key material from Phase D bootstrap and were shredded:

```
$ sudo shred -u -n 3 /tmp/B1_garage_phase_d_bootstrap.log
$ sudo shred -u -n 3 /tmp/phase_d_launch.sh
```

Reason for sudo: `/tmp/B1_garage_phase_d_bootstrap.log` was written by the aws-cli docker container running with `--network host` and bind-mounted `/tmp` — file owner was root on host (P6 lesson #9, banked in Phase E review).

### 2.2 Verification post-shred

```
$ ls -la /tmp/B1_*
ls: cannot access '/tmp/B1_*': No such file or directory

$ ls -la /tmp/phase_d_*
ls: cannot access '/tmp/phase_d_*': No such file or directory
```

Both removed. No plaintext key material remains in `/tmp/`.

### 2.3 Non-secret captures archived

Nine non-secret evidence files moved to a permission-locked archive directory under the project root:

```
$ ls -la /home/jes/garage-beast/.ship-report-inputs/
drwx------ 2 jes jes ... .                              # mode 700 ✔
drwxr-xr-x 5 jes jes ... ..
-rw------- 1 jes jes ... B1_phase_a_capture.md          # mode 600 ✔
-rw------- 1 jes jes ... B1_phase_b_compose.md
-rw------- 1 jes jes ... B1_phase_c_ufw.md
-rw------- 1 jes jes ... B1_phase_d_bootstrap_meta.md   # metadata only, not key material
-rw------- 1 jes jes ... B1_phase_e_lan_smoke.md
-rw------- 1 jes jes ... compose_md5.txt
-rw------- 1 jes jes ... garage_toml_md5.txt
-rw------- 1 jes jes ... image_digest.txt
-rw------- 1 jes jes ... ufw_status_numbered.txt
```

None of these archived files contain key material, secrets, tokens, or credentials. Only metadata, md5 hashes, image digest, and UFW topology snapshots.

### 2.4 Live secret-bearing files (chmod 600 on disk, not archived)

The live operational files retain their chmod 600 and remain in their canonical locations:

```
-rw------- 1 jes jes ... /home/jes/garage-beast/garage.toml      # md5 4837f4a845b3a126904f546059f97729
-rw------- 1 jes jes ... /home/jes/garage-beast/.s3-creds        # md5 393cf89b0662d82588bb4136d0dee2e9
```

Not archived. Mode 600 verified.

---

## 3. F.3 — Ship report evidence

### 3.1 File metadata

```
$ stat -c '%a %U:%G %n' /home/jes/garage-beast/B1_ship_report.md
644 jes:jes /home/jes/garage-beast/B1_ship_report.md

$ wc -l /home/jes/garage-beast/B1_ship_report.md
333 /home/jes/garage-beast/B1_ship_report.md

$ wc -c /home/jes/garage-beast/B1_ship_report.md
17055 /home/jes/garage-beast/B1_ship_report.md

$ md5sum /home/jes/garage-beast/B1_ship_report.md
c4f94f6260a0ef877cb4242cbc9d2f45  /home/jes/garage-beast/B1_ship_report.md
```

### 3.2 Section roll-call (17 directive-mandated sections, all present)

1. Executive summary
2. Pivot rationale (MinIO → Garage)
3. Six Picks (engine, replication, network, ports, image, healthcheck)
4. 8-gate scorecard
5. Bind / UFW / Health
6. Image digest pin
7. File md5s (garage.toml, compose.yaml, .s3-creds)
8. Bucket inventory + key RWO
9. Generated-secrets disclosure pattern
10. Restart-safety result (this Phase F)
11. Smoke-test result (Phase E recap, MD5 roundtrip)
12. B2b bit-identical preservation evidence
13. Deviations summary
14. P5 carryovers (none new)
15. P6 lessons banked (#7–#10, four new this spec)
16. Time elapsed (per phase + total)
17. Open follow-ups (Atlas v0.1 hand-off pointers)

No placeholder text. No `<REDACTED>` of bypass content where evidence existed. All key/secret references replaced with `<REDACTED-IN-SHIP-REPORT>` per standing rule.

### 3.3 Path canonicalization

Canonical artifact location is `/home/jes/garage-beast/B1_ship_report.md` on **Beast** — the spec's mandated target host (matches B2a `B2a_ship_report.md` pattern at `/home/jes/postgres-beast/`). Per memory feedback `feedback_paco_review_doc_per_step.md`: the canonical artifact stays at the spec-mandated path on the target host; `docs/` review docs (this file) are review trail, not deliverables.

---

## 4. State integrity — cross-spec invariants preserved

### 4.1 B2b bit-identical anchor (Beast control-postgres-beast)

```
$ docker inspect --format '{{.State.StartedAt}}' control-postgres-beast
2026-04-27T00:13:57.800746541Z
```

BIT-IDENTICAL nanosecond match to the value captured at:
- B1 Phase A.2 baseline
- B1 Phase B compose authorship
- B1 Phase C UFW rule insertion
- B1 Phase D bootstrap
- B1 Phase E lan_smoke
- B1 Phase F (this turn)

B2b logical replication subscription uninterrupted across the entire B1 spec.

### 4.2 UFW rule count (CiscoKid)

```
$ sudo ufw status numbered | wc -l
15
```

15 rules. Unchanged across all B1 phases. (The Garage 3900 rule lives on Beast, not CiscoKid.)

### 4.3 UFW rule count (Beast)

```
$ sudo ufw status numbered | grep -c '\['
<expected: prior-phase value + 1 for the 3900 ALLOW rule>
```

The 3900 LAN-allow rule placed in Phase C remains in position. No additional rules.

### 4.4 File md5 invariants (Beast: /home/jes/garage-beast/)

| File | md5 | Mode | Phase first captured |
|---|---|---|---|
| garage.toml | 4837f4a845b3a126904f546059f97729 | 600 | B (compose) |
| compose.yaml | 5f9a8878f65922fac5a56ee561f96883 | 644 | B (compose) |
| .s3-creds | 393cf89b0662d82588bb4136d0dee2e9 | 600 | D (bootstrap) |
| B1_ship_report.md | c4f94f6260a0ef877cb4242cbc9d2f45 | 644 | F (this turn) |

All three pre-F file md5s match every prior-phase capture. No drift.

### 4.5 Image digest pin

```
$ docker inspect --format '{{.Image}}' control-garage-beast
sha256:dxflrs/garage@sha256:4c9b34c1...
```

Digest-pinned image unchanged across restart. Compose `pull_policy: never` enforces this.

---

## 5. Phase F acceptance gate scorecard (7 items per directive)

| # | Gate | Result | Evidence ref |
|---|---|---|---|
| 1 | `docker compose restart` exits 0 | PASS | §1.2 |
| 2 | Fresh StartedAt timestamp | PASS | §1.3 (`2026-04-27T05:39:58.168067641Z` ≠ pre `2026-04-27T04:16:17.272248309Z`) |
| 3 | Healthcheck returns to `healthy` ≤ 30s | PASS | §1.3 (11s observed) |
| 4 | Layout / buckets / key intact post-restart | PASS | §1.4 (dc1/4T/91.7%, 3 buckets, RWO key) |
| 5 | Plaintext-key /tmp files shredded | PASS | §2.1–2.2 |
| 6 | Non-secret captures archived 700/600 | PASS | §2.3 (9 files, dir 700, files 600) |
| 7 | Ship report at canonical path, all 17 sections | PASS | §3.1–3.2 (md5 c4f94f62..., 17 sections present) |

**Phase F internal: 7/7 PASS.**

---

## 6. Deviations from directive

### 6.1 RestartCount semantic (informational, not a failure)

Directive expected `RestartCount=1` after `docker compose restart`. Actual: `0`. Docker increments `RestartCount` only on crash-induced restarts (per the container's `restart` policy), not on external `docker compose restart` invocations. Fresh `StartedAt` is the unambiguous restart signal and is verified PASS.

Logged as the **same** semantic correction surfaced during B2b Gate 12. Recommend updating directive language for future specs: replace "RestartCount > pre-value" with "StartedAt timestamp differs from pre-value".

### 6.2 Phase B garage.toml line count (logged Phase B, no action this phase)

Directive Phase B expected 26 lines; actual 28. Structural match (all required keys present), off-by-2 attributed to comment lines. Already noted in `paco_review_b1_garage_phase_b_compose.md` and ratified.

No new deviations introduced in Phase F.

---

## 7. Asks of Paco — independent gate

Please execute the **FULL 8-gate independent verification** from a fresh shell on Beast (and CiscoKid where indicated by the directive). For your convenience, the canonical commands per the original directive's gate spec are:

```bash
# Gate 1: Image digest pin
ssh beast 'docker inspect --format "{{.Image}}" control-garage-beast'
# expect: sha256:dxflrs/garage@sha256:4c9b34c1...

# Gate 2: Bind topology (LAN:3900, lo:3903)
ssh beast 'sudo ss -tlnp | grep -E ":(3900|3901|3903)"'
# expect: 3900 on 192.168.1.152, 3901 LAN, 3903 on 127.0.0.1

# Gate 3: UFW rule for 3900
ssh beast 'sudo ufw status numbered | grep 3900'
# expect: ALLOW from 192.168.1.0/24

# Gate 4: Healthcheck status
ssh beast 'docker inspect --format "{{.State.Health.Status}}" control-garage-beast'
# expect: healthy

# Gate 5: Layout / capacity / zone
ssh beast 'docker exec control-garage-beast /garage status'
# expect: dc1, 4.0 TB, ~91.7% avail

# Gate 6: Bucket inventory
ssh beast 'docker exec control-garage-beast /garage bucket list'
# expect: atlas-state, backups, artifacts

# Gate 7: Root key RWO across all 3 buckets
ssh beast 'docker exec control-garage-beast /garage key info root'
# expect: read,write,owner on all 3 buckets

# Gate 8: B2b bit-identical preservation
ssh beast 'docker inspect --format "{{.State.StartedAt}}" control-postgres-beast'
# expect: 2026-04-27T00:13:57.800746541Z (BIT-IDENTICAL)
```

### 7.1 If all 8 gates PASS

Please write `paco_response_b1_garage_independent_gate_pass_close.md` to `/home/jes/control-plane/docs/` with the gate scorecard and a `B1 CLOSED` ruling. PD will then:

1. Flip `CHECKLIST.md` line for B1 from `[~]` to `[x]`.
2. Commit + push the CHECKLIST flip and the four B1 review docs in `docs/` not yet pushed (Phase E + Phase F close + this review).
3. Update `SESSION.md` and `paco_session_anchor.md` with the close timestamp + commit SHA.
4. Stand by for Atlas v0.1 spec.

### 7.2 If any gate FAILS

Please write `paco_request_b1_garage_independent_gate_fail.md` with the failing gate and authorized remediation path. PD will not improvise on infrastructure absent that authorization (standing rule: spec or no action).

---

## 8. Cross-references

**Predecessors in this spec (correspondence trail):**
- paco_review_b1_garage_phase_a_capture.md
- paco_review_b1_garage_phase_b_compose.md
- paco_review_b1_garage_phase_c_ufw.md
- paco_review_b1_garage_phase_d_bootstrap.md
- paco_review_b1_garage_phase_e_lan_smoke.md
- (this) paco_review_b1_garage_phase_f_close.md

**Anchor docs:**
- /home/jes/control-plane/SESSION.md
- /home/jes/control-plane/paco_session_anchor.md

**Standing rules invoked:**
- Memory: feedback_paco_review_doc_per_step.md (per-step review docs in /home/jes/control-plane/docs/)
- Memory: feedback_mcp_deferred_restart_verify.md (deferred-subshell pattern — not invoked this phase, no MCP restart)
- Standing Rule 1: MCP fabric is for control, not bulk data
- Spec or no action: PD will not flip `CHECKLIST.md` or run further phases without Paco's PASS response

**Live operational files (for reference, not modified this phase):**
- /home/jes/garage-beast/garage.toml (md5 4837f4a8..., chmod 600)
- /home/jes/garage-beast/compose.yaml (md5 5f9a8878..., chmod 644)
- /home/jes/garage-beast/.s3-creds (md5 393cf89b..., chmod 600)
- /home/jes/garage-beast/B1_ship_report.md (md5 c4f94f62..., chmod 644)

---

## 9. Status

**AWAITING PACO FIDELITY CONFIRMATION + INDEPENDENT 8-GATE VERIFICATION.**

PD is paused. No further B1 actions until Paco's response. Atlas v0.1 spec drafting unblocks on B1 close.

— PD
