# paco_review_h1_phase_f_ufw

**Spec:** H1 -- SlimJim observability + MQTT broker close (`tasks/H1_observability.md` section 10)
**Step:** Phase F -- UFW for SlimJim (LAN access for Prometheus :9090 + Grafana :3000) + Phase E corrections folded
**Status:** AWAITING PACO FIDELITY CONFIRMATION + PHASE G GO
**Predecessor:** `docs/paco_response_h1_phase_e_confirm_phase_f_go.md` (commit `dcd41ef`, Phase E confirmed + Option A approved + P6 #17 banked + Phase F GO authorized)
**Author:** PD
**Date:** 2026-04-29 (Day 74)
**Target host:** SlimJim (`192.168.1.40`)

---

## TL;DR

Phase F + 2 Phase E corrections folded into one close-out commit per Paco directive.

- **Phase F 3-gate scorecard 3/3 PASS:** UFW count 5 -> 7 (only 2 new rules); rules 1-5 unchanged; both new rules carry `H1 Phase F:` comments.
- **Correction 1 applied** to spec section 9 E.2 (`GF_SECURITY_ADMIN_PASSWORD_FILE` -> `__FILE`) plus new A.6 subsection banks P6 #17 preflight rule into the spec template forward.
- **Correction 2 applied** to `/home/jes/observability/compose.yaml` (sed _FILE -> __FILE); md5 changed from `b40dd1edd5adb8754b411caaef090f45` to `db89319cad27c091ab1675f7035d7aa3`; `docker compose config` re-passed Gate 2.
- **Standing gate**: B2b + Garage anchors bit-identical pre/post Phase F (postgres `2026-04-27T00:13:57.800746541Z` + garage `2026-04-27T05:39:58.168067641Z`); 19+ phases of H1 work + ~50 hours of operational time, both anchors held.

---

## 1. Phase F execution

### 1.1 UFW pre-state (5 rules)

```
[ 1] 22/tcp        ALLOW IN  192.168.1.0/24
[ 2] 19999/tcp     ALLOW IN  192.168.1.0/24
[ 3] 1883/tcp      ALLOW IN  192.168.1.0/24    # H1 Phase C: Mosquitto LAN
[ 4] 1884/tcp      ALLOW IN  192.168.1.0/24    # H1 Phase C: Mosquitto LAN authed
[ 5] 9100/tcp      ALLOW IN  127.0.0.1         # H1 Phase E.4: node_exporter local scrape
```

### 1.2 Phase F UFW additions (verbatim from spec section 10)

```bash
sudo ufw allow from 192.168.1.0/24 to any port 9090 proto tcp comment 'H1 Phase F: Prometheus LAN'
sudo ufw allow from 192.168.1.0/24 to any port 3000 proto tcp comment 'H1 Phase F: Grafana LAN'
```

Both returned `Rule added` exit 0.

### 1.3 UFW post-state (7 rules)

```
[ 1] 22/tcp        ALLOW IN  192.168.1.0/24
[ 2] 19999/tcp     ALLOW IN  192.168.1.0/24
[ 3] 1883/tcp      ALLOW IN  192.168.1.0/24    # H1 Phase C: Mosquitto LAN
[ 4] 1884/tcp      ALLOW IN  192.168.1.0/24    # H1 Phase C: Mosquitto LAN authed
[ 5] 9100/tcp      ALLOW IN  127.0.0.1         # H1 Phase E.4: node_exporter local scrape
[ 6] 9090/tcp      ALLOW IN  192.168.1.0/24    # H1 Phase F: Prometheus LAN     (NEW)
[ 7] 3000/tcp      ALLOW IN  192.168.1.0/24    # H1 Phase F: Grafana LAN        (NEW)
```

---

## 2. Phase F 3-gate scorecard

| Gate | Spec wording | Live observed | Result |
|---|---|---|---|
| 1 | UFW count 5 -> 7 (only 2 new rules added) | 5 -> 7 | **PASS** |
| 2 | No existing rules modified or removed (rules 1-5 unchanged) | rules [1]-[5] visually byte-identical pre/post | **PASS** |
| 3 | Both new rules carry H1 Phase F comments | rule [6] `# H1 Phase F: Prometheus LAN`, rule [7] `# H1 Phase F: Grafana LAN` | **PASS** |
| Standing | B2b + Garage anchors bit-identical pre/post | postgres `2026-04-27T00:13:57.800746541Z` + garage `2026-04-27T05:39:58.168067641Z`, both healthy 0 restarts | **PASS** |

**Phase F internal scorecard: 3/3 PASS + standing PASS.**

---

## 3. Correction 2 evidence (compose.yaml on-disk fix)

### 3.1 Pre + post md5

```
Pre  (Phase E close):  b40dd1edd5adb8754b411caaef090f45
Post (this commit):    db89319cad27c091ab1675f7035d7aa3
```

### 3.2 Sed command applied

```bash
sed -i 's/GF_SECURITY_ADMIN_PASSWORD_FILE/GF_SECURITY_ADMIN_PASSWORD__FILE/' /home/jes/observability/compose.yaml
```

### 3.3 Env section verification post-correction

```yaml
    environment:
      GF_SECURITY_ADMIN_PASSWORD__FILE: /run/secrets/grafana_admin_pw
```

Double underscore confirmed. Phase G's smoke test "Grafana login works with admin + CEO password" will now read CEO's grafana-admin.pw content correctly.

### 3.4 Gate 2 re-pass

`docker compose config /home/jes/observability/compose.yaml` returned exit 0 with the corrected env var. compose.yaml structurally valid.

---

## 4. Correction 1 evidence (spec amendment)

The authoritative spec text in `tasks/H1_observability.md` is now corrected at section 9 E.2:

**Before** (line 374, pre-amendment):
```yaml
      GF_SECURITY_ADMIN_PASSWORD_FILE: /run/secrets/grafana_admin_pw
```

**After** (line 374, post-amendment):
```yaml
      GF_SECURITY_ADMIN_PASSWORD__FILE: /run/secrets/grafana_admin_pw  # double underscore: Grafana 11.x file-provider convention (Correction 1, banked P6 #17 Phase E close 2026-04-29)
```

**Plus new section A.6** banks P6 #17 forward as a preflight rule for any future spec phase that references upstream-product env var conventions.

Spec md5 changes:
```
Pre  (Phase D close + A.5 amend):  71aaf1ef4a182b1377d8a28b256c55d1
Post (this commit):                 a81e24c8ee3e66b2cb4a74dc9abac2cd
```

Line count: 600 -> 608 (+8 lines: 1 line for inline comment expansion at 374, +7 lines for A.6 subsection).

---

## 5. Beast anchor preservation evidence

Phase F + 2 corrections touched only:
- `/home/jes/observability/compose.yaml` (Correction 2 sed)
- SlimJim UFW (2 rule additions)
- `tasks/H1_observability.md` on CiscoKid (Correction 1 surgical edit)

**No Beast service touched.**

```
# Pre-Phase-F (captured as part of Step 3):
/control-postgres-beast StartedAt=2026-04-27T00:13:57.800746541Z
/control-garage-beast   StartedAt=2026-04-27T05:39:58.168067641Z

# Post-Phase-F (captured as part of Step 3):
/control-postgres-beast StartedAt=2026-04-27T00:13:57.800746541Z
/control-garage-beast   StartedAt=2026-04-27T05:39:58.168067641Z
```

**BIT-IDENTICAL nanosecond match.** **19+ phases of H1 work + ~50 hours of operational time, both anchors held.**

---

## 6. Phase G concern carry-forward (still open)

Flagged at Phase E close, unchanged this phase. When the Prom container starts at Phase G compose-up, outbound scrape to `192.168.1.40:9100` will go through Docker bridge NAT. Source IP will be the bridge gateway (typically `172.17.0.1` or compose project's bridge subnet), NOT `127.0.0.1`. UFW rule [5] (`from 127.0.0.1`) won't match the container's NAT'd source.

Paco's response §3.2 (Phase G concern) enumerated paths:
- **Path 1**: Add UFW rule from compose project's bridge subnet for port 9100. Increases UFW surface but matches actual scrape source.
- (other paths Paco may enumerate at Phase G ruling time: switch Prom to `network_mode: host`; change prometheus.yml SlimJim target to `127.0.0.1:9100`)

**Phase G preflight item**: at Phase G compose-up time, observe Prom logs for the SlimJim self-scrape target. If it shows `connection refused` or similar, the bridge-NAT issue is real and Paco rules at Phase G review on which path to apply. If Linux local routing optimization or Docker daemon's userland-proxy handling routes the same-host LAN-IP scrape through lo, the issue may not manifest. Either outcome is a Phase G discovery; Phase E + F tear off the operational config + firewall layers; Phase G validates runtime.

---

## 7. State at close

### SlimJim observability stack

- 6 config files written (md5 of compose.yaml updated to `db89319cad27c091ab1675f7035d7aa3`; other 5 unchanged)
- 2 image digests pinned in compose.yaml + cached in docker images list
- 5th node_exporter installed (Phase E.4) + UFW rule [5] for local scrape
- UFW: 7 rules (5 -> 7 this phase)
- Containers DOWN (Phase G is when they come up)
- grafana-admin.pw placeholder chmod 600 (CEO writes content pre-Phase-G)

### Beast (read-only confirmation)

- both anchors bit-identical pre/post Phase F
- B2b logical replication subscriber: continuous
- Garage S3 substrate: continuous

### CiscoKid (read-only confirmation)

- HEAD before this commit: `65e3fd4` (`feat: bank Paco-PD handoff protocol as standing rule (memory file)`)
- This commit folds: spec amendment + paco_review + SESSION + anchor + CHECKLIST = 5 files
- observability/ files live on SlimJim filesystem (operational config), NOT in control-plane.git

---

## 8. Asks of Paco

1. **Confirm Phase F 3/3 gates PASS** against captured evidence (sections 1 + 2).
2. **Confirm Correction 1 + Correction 2 applied correctly** per Option A authorization (sections 3 + 4).
3. **Authorize Phase G GO** -- compose up + healthcheck per spec section 11. CEO writes grafana-admin.pw content before compose-up. Phase G concern (bridge NAT vs UFW [5]) ruled at Phase G time when behavior observable.
4. **Acknowledge P6 #17 spec amendment landed** in `tasks/H1_observability.md` A.6.

---

## 9. Cross-references

**Standing rules invoked:**
- Memory: `feedback_paco_review_doc_per_step.md` (per-step review docs in `/home/jes/control-plane/docs/`)
- Memory: `feedback_directive_command_syntax_correction_pd_authority.md` (5-guardrail rule + carve-out for ops propagation; guardrail 5 self-catch on Grafana env var was the trigger for Correction 1 + 2)
- Spec or no action: PD applied Corrections 1 + 2 only after Paco's Option A ratification
- B2b + Garage nanosecond invariant preservation

**Predecessor doc chain:**
- `paco_review_h1_phase_e_observability_skeleton.md` (commit `172176f`, Phase E 4/4 + spec discrepancy flag)
- `paco_response_h1_phase_e_confirm_phase_f_go.md` (commit `dcd41ef`, Phase E confirmed + Option A approved + P6 #17 banked + Phase F GO)
- (this) `paco_review_h1_phase_f_ufw.md`

## 10. Status

**AWAITING PACO FIDELITY CONFIRMATION + PHASE G GO.**

PD paused. Phase F 3/3 PASS + Corrections 1 + 2 applied + 19-phase B2b/Garage anchor preservation continues. Containers DOWN until Phase G compose-up. UFW final state at 7 rules. CEO's grafana-admin.pw content prerequisite for Phase G.

-- PD
