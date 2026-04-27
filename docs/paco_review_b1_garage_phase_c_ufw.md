# PD -> Paco review -- B1-Garage Phase C: UFW allow for port 3900 (S3 LAN)

**From:** PD (Head of Engineering, Cowork)
**To:** Paco (COO, claude.ai)
**Date:** 2026-04-26 (Day 72)
**Spec:** `tasks/B1_garage_beast.md` Phase C
**Authorization:** `docs/paco_response_b1_garage_phase_b_confirm_phase_c_go.md`
**Phase:** C of 6 (A-F) for Garage track
**Status:** **AWAITING PACO FIDELITY CONFIRMATION** before Phase D (deferred-subshell bootstrap: container start + healthcheck + cluster layout + S3 root key + 3 buckets + .s3-creds)
**Predecessor:** `docs/paco_review_b1_garage_phase_b_compose.md`

---

## TL;DR

One UFW rule added: `ufw allow from 192.168.1.0/24 to any port 3900 proto tcp comment 'B1: Garage S3 API'`. Rule lands at position **[15]** (end of table), no DENY collision. **No service-affecting changes** -- B2b control-postgres-beast bit-identical pre/post (StartedAt nanosecond match), Garage ports 3900-3904 still unbound (no container started yet). Beast staged for Phase D.

---

## Step C.1 -- UFW allow execution

### Pre-rule baseline

```
UFW rule count:                   14
B2b control-postgres-beast:       Up 4 hours (healthy), 127.0.0.1:5432
  PRE-C StartedAt:                2026-04-27T00:13:57.800746541Z
  RestartCount:                    0
```

### Command + result

```
$ sudo ufw allow from 192.168.1.0/24 to any port 3900 proto tcp comment 'B1: Garage S3 API'
Rule added

$ sudo ufw status numbered | grep '3900'
[15] 3900/tcp                   ALLOW IN    192.168.1.0/24             # B1: Garage S3 API
```

### Post-rule UFW snapshot

```
File:                             /tmp/B1_garage_phase_c_ufw_post.txt
Lines:                            20
Size:                             1483 bytes
md5:                              934f41fdaa3aba85709e2798ee7c2805
Rule count:                       15  (was 14, +1)
```

### New rule position

```
[14] 8800/tcp                   ALLOW IN    192.168.1.0/24                                         <-- pre-existing (last before B1)
[15] 3900/tcp                   ALLOW IN    192.168.1.0/24             # B1: Garage S3 API         <-- NEW (this turn)
```

The new rule lands cleanly at `[15]`, immediately after the existing `8800/tcp` LAN-allow. This validates the directive's prediction (no DENY collision; simple `ufw allow ...` lands at end). Differs from B2b's case where 5432 had pre-existing IoT-DENY at position [18] requiring `ufw insert`.

### Sample of preserved [1]-[5] rules (intact verification)

```
[ 1] Anywhere   DENY IN   192.168.1.221   # BLOCK IoT: Eufy vacuum
[ 2] Anywhere   DENY IN   192.168.1.111   # BLOCK IoT: Samsung Fridge
[ 3] Anywhere   DENY IN   192.168.1.191   # BLOCK IoT: Samsung Range
[ 4] Anywhere   DENY IN   192.168.1.125   # BLOCK IoT: Samsung TV
[ 5] Anywhere   DENY IN   192.168.1.176   # BLOCK IoT: WiZ bulb 4
```

14 pre-existing rules confirmed intact at original positions; only addition is the new rule at [15].

---

## 5-gate acceptance scorecard (5/5 PASS)

| # | Gate | Result | Evidence |
|---|---|---|---|
| 1 | New ALLOW for 3900/tcp from 192.168.1.0/24 at end of UFW (position [15]) | **PASS** | `[15] 3900/tcp ALLOW IN 192.168.1.0/24` |
| 2 | Documented comment present (`B1: Garage S3 API`) | **PASS** | `COMMENT_PRESENT` (`# B1: Garage S3 API`) |
| 3 | All 14 pre-existing rules still present in [1]-[14]; total = 15 | **PASS** | `TOTAL_15_OK`; sample [1]-[5] verified IoT DENY rules intact |
| 4 | /tmp capture file written + md5 captured | **PASS** | 1483 bytes, md5 `934f41fdaa3aba85709e2798ee7c2805` |
| 5 | NO service-affecting changes (B2b bit-identical, ports 3900-3904 still unbound) | **PASS** | StartedAt `2026-04-27T00:13:57.800746541Z` nanosecond-identical, RestartCount=0; Garage ports all free |

## Gate 5 detail (B2b infrastructure unchanged)

```
control-postgres-beast (B2b subscriber):
  Status:           Up 4 hours (healthy), 127.0.0.1:5432->5432/tcp
  StartedAt:        2026-04-27T00:13:57.800746541Z
                    ^^^^ IDENTICAL across Phase A2, Phase B, and Phase C ^^^^
  RestartCount:     0

Garage listeners:
  3900 (S3 API):    not bound (Phase D will start container)
  3901 (RPC):       not bound
  3902 (web):       not bound
  3903 (admin):     not bound
  3904 (k2v):       not bound
```

UFW rule alone does not create a listener -- the rule exists at the firewall level; the listener will appear once Phase D starts the container. Until then, the new rule is dormant (no traffic to filter).

## State of Beast at end of Phase C

```
Directory tree:                   unchanged from Phase B
  /home/jes/garage-beast/         config dir, jes:jes 775
    garage.toml                   679 bytes / 0600 / md5 4837f4a8... (SECRETS)
    compose.yaml                  586 bytes / 0664 / md5 5f9a8878...
  /home/jes/garage-data/{meta,data}  empty 0700

Docker:                           unchanged from Phase B
  control-postgres-beast          Up 4 hours (healthy), B2b unchanged
  control-garage-beast            not yet created (Phase D)
  Images:                         dxflrs/garage:v2.1.0 (digest 4c9b34c1..., ~25 MiB) pulled

Network:
  UFW                             15 rules (14 pre-existing + 1 new B1 rule at [15])
  Listeners 3900-3904             all free (no container)
  Listener 5432                   127.0.0.1 (B2a unchanged)
```

## Phase D preview (informational, not yet authorized)

Phase D is the most procedurally complex phase. Per Garage spec Phase D:

1. **Container start** -- `docker compose up -d` brings up `control-garage-beast`
2. **Healthcheck poll** -- wait for `mc ready local` equivalent (or `/garage status` exit 0); cap ~60-90s
3. **Cluster layout** -- single-node Garage requires explicit `garage layout assign` + `garage layout apply`:
   - `docker exec control-garage-beast /garage layout assign --node-id <self> --capacity 100GB --zone home`
   - `docker exec control-garage-beast /garage layout apply`
4. **Root S3 key creation** -- `garage key new --name root` returns access_key + secret_key
5. **3 bucket creates + grants** -- `garage bucket create atlas-state`, `backups`, `artifacts`, then `garage bucket allow --read --write --owner --key root <bucket>`
6. **Write `.s3-creds`** -- `/home/jes/garage-beast/.s3-creds` chmod 600, with AWS_ACCESS_KEY_ID/SECRET_ACCESS_KEY/REGION/ENDPOINT_URL exports

**Approach per Paco's directive:** deferred-subshell pattern (B2b precedent). Subshell logs to `/tmp/B1_garage_phase_d_bootstrap.log`; survives any session disruption during the multi-step bootstrap. Verification queries Garage state externally after subshell completes.

**Secret-redaction discipline carries over:** the access/secret key generated by `garage key new` will be captured into .s3-creds on disk, but will NOT be echoed in the review doc.

## Asks of Paco

1. Confirm Phase C fidelity:
   - 1 new rule at [15], 3900/tcp ALLOW IN 192.168.1.0/24 with comment `B1: Garage S3 API`
   - Total UFW count: 15 (was 14)
   - 14 pre-existing rules intact at original positions
   - Capture file md5: `934f41fdaa3aba85709e2798ee7c2805`
   - B2b bit-identical pre/post (StartedAt nanosecond match)
2. **Go for Phase D** -- deferred-subshell bootstrap (container start + healthcheck poll + cluster layout assign+apply + root S3 key creation + 3 bucket creates + 3 grants + .s3-creds write)

## Standing rules in effect

- **Rule 1:** Phase C = 1 sudo ufw command + 1 capture write. Compliant.
- **CLAUDE.md "Spec or no action":** literal `ufw allow ...` per directive. No deviations.
- **CLAUDE.md "Docker bypasses UFW":** rule added; still defense-in-depth posture; admin port 3903 stays localhost-only (no UFW rule needed). Real gates remain LAN-bind + S3 access key auth (key created Phase D).
- **Correspondence protocol:** this is paco_review #3 in the new B1-Garage chain.
- **Canon location:** UFW state on Beast (workspace); review doc on CiscoKid (canon). Per memory edit #20.

---

**File location:** `/home/jes/control-plane/docs/paco_review_b1_garage_phase_c_ufw.md` (untracked, matches /docs precedent)

-- PD
