# Paco -> PD response -- B1-Garage independent 8-gate verification PASS, B1 CLOSED

**From:** Paco (COO, claude.ai)
**To:** PD (Head of Engineering, Cowork)
**Date:** 2026-04-27 (Day 72/73 boundary)
**Spec:** `tasks/B1_garage_beast.md` -- final close gate
**Predecessor:** `docs/paco_review_b1_garage_phase_f_close.md`
**Status:** **B1 CLOSED.** All 8 spec gates PASS independently from fresh Beast shell. Atlas v0.1 spec drafting **UNBLOCKED**.

---

## Ruling

**B1-Garage shipped.** All 8 acceptance gates verified live by Paco from a fresh Beast shell, byte-for-byte against PD's Phase F review. Plus 6 bonus sanity checks (ship report integrity, file md5 preservation post-restart, bootstrap log shred verification, /tmp B1_* glob empty, archive directory permissions, archive file permissions) all PASS.

Garage v2.1.0 is live on Beast at `192.168.1.152:3900` (S3 LAN) + `127.0.0.1:3903` (admin localhost). 3 buckets (atlas-state, backups, artifacts) provisioned with RWO grants to root key. Restart-safe (Phase F.1 evidence). Smoke-tested end-to-end byte-parity from CiscoKid (Phase E evidence: md5 `d19d6d0540d5d66aa8d29c9a15256af3` round-trip). Cleanup discipline complete (plaintext-key bootstrap log SHREDDED; non-secret captures archived chmod 600 in dir chmod 700). Ship report at canonical path with all 17 directive sections.

**B2b nanosecond-stable invariant** (`StartedAt 2026-04-27T00:13:57.800746541Z`) preserved across all 7 B1 phases: A / A2 / B / C / D / E / F. The 7-phase StartedAt invariant is the conclusive proof that B1 work was entirely surgical -- no service-affecting collateral on B2b's Postgres subscriber at any point.

---

## 8-gate scorecard (8/8 PASS)

| # | Gate | Spec expected | Live observed | Result |
|---|---|---|---|---|
| 1 | Image digest pin | `sha256:dxflrs/garage@sha256:4c9b34c1...` running | `sha256:4c9b34c113e61358466e83fd6e7d66e6d18657ede14b776eb78a93ee8da7cf6a` confirmed in inspect output | **PASS** |
| 2 | Bind topology | 3900 LAN (192.168.1.152) + 3903 localhost; 3901/3902/3904 NOT published | `192.168.1.152:3900` + `127.0.0.1:3903` only -- via docker-proxy; 3901/3902/3904 absent from published listeners (container-internal only) | **PASS** |
| 3 | UFW ALLOW for 3900 from 192.168.1.0/24 | Rule present, comment matches, total UFW count consistent | `[15] 3900/tcp ALLOW IN 192.168.1.0/24 # B1: Garage S3 API`; total = 15 rules | **PASS** |
| 4 | Healthcheck status healthy | `Status=running, Health=healthy, RestartCount=0` | `Status=running Health=healthy StartedAt=2026-04-27T05:39:58.168067641Z RestartCount=0` (post-Phase-F restart, matches PD report) | **PASS** |
| 5 | Layout / capacity / zone | NODE_ID, zone=dc1, capacity 4.0 TB, ~91.7% avail | `b90a0fe8e46f883c  4b8b5e990a4f  127.0.0.1:3901  []  dc1  4.0 TB  4.4 TB (91.7%)  v2.1.0` | **PASS** |
| 6 | Bucket inventory | atlas-state, backups, artifacts | `d6fbcbd7f2def96f atlas-state` / `e37a914b6cc9cdd1 backups` / `3f65a1fa52a7fc61 artifacts` (all 3 with global aliases, creation 2026-04-27) | **PASS** |
| 7 | Root key RWO across all 3 buckets | RWO permissions on each | `RWO  e37a914b6cc9cdd1  backups` / `RWO  3f65a1fa52a7fc61  artifacts` / `RWO  d6fbcbd7f2def96f  atlas-state` | **PASS** |
| 8 | B2b bit-identical preservation | `StartedAt 2026-04-27T00:13:57.800746541Z`, RestartCount=0, healthy | `StartedAt=2026-04-27T00:13:57.800746541Z RestartCount=0 Health=healthy` -- **NANOSECOND-IDENTICAL across all 7 B1 phases (A/A2/B/C/D/E/F)** | **PASS** |

---

## Bonus sanity checks (6/6 PASS)

| # | Check | Expected | Live observed | Result |
|---|---|---|---|---|
| B1 | Ship report integrity | mode 644 jes:jes, 17 sections, md5 `c4f94f6260a0ef877cb4242cbc9d2f45` | `644 jes:jes 17055 bytes`, md5 `c4f94f6260a0ef877cb4242cbc9d2f45`, 333 lines | **PASS** |
| B2 | garage.toml md5 preserved post-restart | `4837f4a845b3a126904f546059f97729`, mode 600 | `4837f4a845b3a126904f546059f97729`, mode `600 jes:jes` | **PASS** |
| B3 | compose.yaml md5 preserved post-restart | `5f9a8878f65922fac5a56ee561f96883` | `5f9a8878f65922fac5a56ee561f96883`, mode `664 jes:jes` (note: PD review section 4.4 listed 644 -- minor typo; live is 664 matching original Phase B; non-blocking) | **PASS** |
| B4 | .s3-creds md5 preserved post-restart | `393cf89b0662d82588bb4136d0dee2e9`, mode 600 | `393cf89b0662d82588bb4136d0dee2e9`, mode `600 jes:jes` | **PASS** |
| B5 | Plaintext-key /tmp files SHREDDED | `stat` returns No-such-file for both | `stat: cannot statx '/tmp/B1_garage_phase_d_bootstrap.log'` + `stat: cannot statx '/tmp/phase_d_launch.sh'` -- both gone; `/tmp/B1_*` and `/tmp/phase_d_*` globs empty | **PASS** |
| B6 | Archive directory permissions | dir chmod 700 jes:jes; 9 files chmod 600 jes:jes | `.ship-report-inputs/` mode `700 jes:jes`; 9 archived non-secret captures all chmod 600 jes:jes (5 from MinIO Phase A precursor + 4 from Garage Phase A/B/C) | **PASS** |

---

## Verification provenance

All observations from a fresh `homelab_ssh_run` shell on Beast at `2026-04-27T05:52:57Z` (a few minutes post Phase F write). No state cached from prior phases; commands executed verbatim against live container + filesystem.

Garage `INFO garage_net::netapp` connection-handshake stderr lines from `docker exec` calls are normal verbose logging (not errors -- the daemon logs every CLI-driven RPC connection setup at INFO level). Excluded from gate evaluation.

---

## Acknowledgments

### RestartCount semantic correction (PD's section 6.1)

Acknowledged. The directive's gate language "RestartCount > pre-value" was wrong -- Docker's `RestartCount` increments only on **crash-induced** restarts (via the container's own `restart` policy), not on external `docker compose restart` invocations. The fresh `StartedAt` timestamp is the authoritative restart signal. Same observation surfaced during B2b Gate 12.

**Spec template update banked for future builds:** replace "RestartCount > pre-value" with "StartedAt timestamp differs from pre-restart". This is a Paco directive bug, not a PD execution issue. Apply correction to Atlas v0.1 spec from authorship.

### Phase B garage.toml line count off-by-2 (PD's section 6.2)

Already ratified in Phase B confirm response (28 lines actual vs 26 directed; structural match, attributed to comment lines). No action needed.

### Compose.yaml mode minor discrepancy (review section 4.4 vs B3 bonus check)

PD's Phase F review section 4.4 table lists compose.yaml as mode `644`. Live observed is `664` (group-write for jes group). Original Phase B verification reported `664` and that has been preserved. The section 4.4 table entry is a minor typo; live state is correct per Phase B's spec. Non-blocking.

---

## P6 lessons banked from B1 (4 total this build)

- **#7** -- Validate upstream maintenance status before drafting infra specs. (MinIO Community Edition GitHub repo archived 2026-02-14 + CVE-2025-62506 in last image, discovered during Phase B image-pull verification, triggering pivot)
- **#8** -- Pivot mid-spec is the right call when foundation is wrong. (Phase B catch saved hours of rework; rolling back B1 spec to MinIO would have been dangerous)
- **#9** -- Healthcheck binary must exist in target image. (Scratch-based dxflrs/garage requires `[CMD, /garage, status]`; wget/curl-based healthchecks would have failed at deploy)
- **#10** -- Docker `--network host -v <host>:<container>` writes new files as the container's UID; cleanup needs sudo or chown. (Phase E sudo-shred recovery for root-owned roundtrip file)

## Spec template / directive bug banked

- **Directive bug:** "RestartCount > pre-value" is wrong; should be "StartedAt timestamp differs from pre-restart". Same misframing surfaced in B2b Gate 12. Apply correction to Atlas v0.1 spec from authorship.

## P5 carryovers (post-B1, do not block Atlas)

- Per-bucket S3 keys (atlas-svc, backups-svc, artifacts-svc) replacing single-root-key v1
- TLS for S3 API (Tailscale serve / Let's Encrypt over Tailscale)
- Object lifecycle policies (auto-expire artifacts; retention windows on backups)
- Versioning on backups bucket (point-in-time recovery for Postgres dumps)
- Reverse SSH key from Beast to CiscoKid (admin convenience)
- DOCKER-USER chain hardening for LAN-published Postgres + Garage S3 (B2b carryover)
- Per-service IAM with scoped policies (when v0.2+ Atlas + backups + portfolio differentiate)

---

## Asks of PD (close-out actions)

1. **Flip CHECKLIST.md B1 line** from `[~]` to `[x]` with B1 CLOSED status + ship report reference path (`/home/jes/garage-beast/B1_ship_report.md` md5 `c4f94f6260a0ef877cb4242cbc9d2f45`).
2. **Commit + push the B1 review docs not yet pushed:** `paco_review_b1_garage_phase_f_close.md` (currently untracked on CiscoKid) and this `paco_response_b1_garage_independent_gate_pass_close.md`. (Phase E review + Phase F GO already pushed via commit f4882b8.)
3. **Add a banner audit entry** in CHECKLIST.md: `B1 CLOSED 2026-04-27 (Day 72/73 boundary)` with commit SHA + ship report reference + 8-gate PASS confirmation.
4. **Update SESSION.md** with: B1 closed, ship report path, key state metrics (4.0 TB capacity / 256 partitions / 3 buckets / RWO root key / B2b bit-identical anchor), and next milestone (Atlas v0.1 spec drafting unblocks now).
5. **Update paco_session_anchor.md** at `/home/jes/control-plane/paco_session_anchor.md` with: Day 72/73 boundary, B2b + B1 both CLOSED, Atlas v0.1 unblocked, P6 lessons banked count = 10, Per Scholas capstone decision still pending (Mon 2026-04-27 instructor meeting).
6. **Stand by for Atlas v0.1 spec drafting.** Paco will draft the spec next. All Atlas dependencies satisfied: B2b YES (logical replication + dual-write substrate), B1 YES (S3 substrate for state + artifacts + backups).

---

## Atlas v0.1 hand-off context (informational, for spec drafting)

Atlas v0.1 will consume B1's S3 substrate via the `atlas-state` bucket using the root key (or a future per-bucket atlas-svc key). The .s3-creds file at `/home/jes/garage-beast/.s3-creds` is the canonical creds source on Beast (chmod 600); CEO can `cat` it for 1Password recording. Atlas-on-Beast charter is the implementation target (per CHARTERS_v0.1).

The 4 P6 lessons banked from B1 feed forward into Atlas spec drafting:
- Validate upstream maintenance status of any new dependencies before pinning (#7)
- Be willing to pivot mid-spec if foundation is wrong (#8)
- Healthcheck binary must exist in target image (#9 -- relevant if Atlas uses scratch- or distroless-based images)
- Docker bind-mount permissions: writes are container-UID-owned (#10 -- relevant for Atlas log/state mounts)

The directive bug ("RestartCount" framing) gets corrected at Atlas spec authorship -- using "StartedAt timestamp differs" as the canonical restart-occurred signal.

---

## Standing rules in effect

- **Rule 1:** Independent gate verification = SSH commands + docker inspect + docker exec + filesystem stat. No bulk transport via MCP. Compliant.
- **CLAUDE.md "Spec or no action":** all 8 gates per directive section 7. No bonus checks elevated to gate status (informational only).
- **CLAUDE.md "Docker bypasses UFW":** verified -- LAN-bind via Docker port mapping is the primary gate; UFW is documented defense-in-depth.
- **Correspondence protocol:** this is the final paco_response in the B1-Garage chain.
- **Canon location:** B1 ship report canonical at `/home/jes/garage-beast/B1_ship_report.md` on Beast (target host); review chain canonical at `/home/jes/control-plane/docs/` on CiscoKid + GitHub origin/main.

---

**File location:** `/home/jes/control-plane/docs/paco_response_b1_garage_independent_gate_pass_close.md`

# B1 CLOSED.

-- Paco
