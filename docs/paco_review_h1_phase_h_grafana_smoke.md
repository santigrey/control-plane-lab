# paco_review_h1_phase_h_grafana_smoke

**Spec:** H1 -- Phase H Grafana smoke + LAN smoke from CK + CEO browser test (`tasks/H1_observability.md` section 12)
**Status:** Phase H **CLOSED 4/4 LITERAL PASS** under the new standing closure pattern (`docs/feedback_phase_closure_literal_vs_spirit.md`). One known limitation at ship documented + P5 carryover banked.
**Date:** 2026-04-29 (Day 74)
**Author:** PD
**Predecessor docs:**
- `paco_response_h1_phase_g_confirm_phase_h_go.md` (commit `d3d8ced`)
- `paco_request_h1_phase_h_prometheus_dashboard_fail.md` (PD ESC #1 of Phase H)
- `paco_response_h1_phase_h_path_a_approved.md` (commit `0326903`, Path A approved + standing closure pattern banked)
- `feedback_phase_closure_literal_vs_spirit.md` (4th standing rule memory file, Paco-authored this turn)

---

## 1. TL;DR

Phase H structural acceptance: **4/4 literal PASS**. Grafana stack (obs-prometheus + obs-grafana) running healthy on SlimJim. CEO browser tests confirmed login + both dashboards visible + Node Exporter Full rendering live data from SlimJim's node_exporter (CPU 1.7% / RAM 4.8% / disk 25.3% / network kb/s / 6.3 day uptime).

One known limitation at ship: dashboard 3662 (Prometheus 2.0 Overview) renders all panels N/A under Grafana 11.3.0. Root cause is dashboard-internal (deprecated singlestat panel + old variable query syntax; Grafana 11 auto-migration insufficient). Datasource + provisioning + container stack are healthy (Node Exporter Full proves this with the same datasource). Banked as P5 carryover for v0.2 hardening pass with 3 candidate replacements identified.

Closed under the new standing closure pattern (literal-PASS + spirit-partial -> close + P5 when 5 conditions hold). All 5 conditions verified satisfied for this case.

B2b + Garage anchors bit-identical pre/post entire Phase H (read-only Phase, expected). 19+ phases of operational work / ~52 hours / zero substrate disturbance.

---

## 2. Phase H 4-gate scorecard

| Gate | Description | Status | Evidence |
|------|-------------|--------|----------|
| 1 | Grafana web HTTP 200 + login page renders | PASS | CEO browser confirm |
| 2 | CEO login succeeds with admin + grafana-admin.pw | PASS | CEO browser confirm |
| 3 | Both provisioned dashboards visible in Dashboards menu | PASS | CEO browser confirm (1860 + 3662 both visible) |
| 4 | Dashboards render with live data from at least one node_exporter target | PASS | Node Exporter Full = SlimJim 192.168.1.40:9100, CPU 1.7%, RAM 4.8%, full panel render |

Plus standing gate: B2b + Garage anchors bit-identical pre/post -- PASS (read-only Phase H).

**4/4 literal PASS.**

---

## 3. Container final state

```
obs-prometheus  Status=running Health=healthy        Restarts=0
obs-grafana     Status=running Health=(no-healthcheck)  Restarts=0
```

7/7 Prometheus targets up (unchanged from Phase G close). compose.yaml unchanged (md5 `db89319cad27c091ab1675f7035d7aa3`, Phase F state). UFW unchanged (9 rules per Phase G close).

---

## 4. PD-side filesystem provisioning evidence (in-container)

### 4.1 Datasource provisioning

```
/etc/grafana/provisioning/datasources/datasource.yml
  apiVersion: 1
  datasources:
    - name: Prometheus
      type: prometheus
      access: proxy
      url: http://prometheus:9090
      isDefault: true
```

Verified via `docker exec obs-grafana cat /etc/grafana/provisioning/datasources/datasource.yml`.

### 4.2 Dashboard provisioning

```
/etc/grafana/provisioning/dashboards/dashboard.yml
  apiVersion: 1
  providers:
    - name: 'default'
      orgId: 1
      folder: ''
      type: file
      disableDeletion: false
      options:
        path: /var/lib/grafana/dashboards
```

### 4.3 Dashboard JSON files visible inside container

```
/var/lib/grafana/dashboards/
  node-exporter-full.json     468,600 bytes
  prometheus-stats.json        85,625 bytes
```

Both provisioned files mounted + readable by container UID 472.

### 4.4 Grafana log scan -- 4 benign warning classes cataloged

- `plugin xychart is already registered` -- Grafana 11 internal panel double-registration, benign, panel still works
- `open /etc/grafana/provisioning/plugins: no such file or directory` -- optional plugins/ provisioning subdir not configured, benign
- `open /etc/grafana/provisioning/alerting: no such file or directory` -- optional alerting/ provisioning subdir not configured, benign
- `Database locked, sleeping then retrying` -- SQLite transient lock, retry succeeded, no escalation

None blocking. Standard Grafana 11.3.0 startup noise on a minimal-provisioning configuration.

---

## 5. CEO browser test results

### 5.1 Node Exporter Full (dashboard 1860) -- PASS

CEO confirmed full panel render with live data:

- Datasource dropdown: `Prometheus` (resolved cleanly)
- Job: `node` (resolved)
- Nodename: `sloan1` (resolved)
- Instance: `192.168.1.40:9100` (resolved -- SlimJim self)
- Time range: Last 24 hours (rendering live data)
- Quick numbers: CPU 1.7% / RAM 4.8% / Root FS 25.3% / 31 GiB total RAM / 271 GiB total disk / Uptime 6.3 days
- Time-series panels (CPU Basic / Memory Basic / Network Traffic Basic / Disk Space Used Basic): all rendering live data with proper timeline

This confirms (a) Prometheus datasource is healthy + connected, (b) provisioning files mounted + parsed correctly, (c) datasource UID resolution working, (d) Grafana -> Prometheus container-to-container connectivity working, (e) Prometheus has data flowing from node_exporter, (f) dashboard 1860 is Grafana-11-compatible.

Gate 4 satisfied by Node Exporter Full alone.

### 5.2 Prometheus 2.0 Overview (dashboard 3662) -- FAIL (known limitation)

CEO confirmed all panels show N/A. Variable dropdowns (`job`, `instance`) show warning triangles -- variable queries failing to resolve. One panel shows literal text: `"Panel plugin has no panel component"` -- deprecated singlestat panel removed in Grafana 11.x.

Failure pattern is uniform across the dashboard, confirming it is dashboard-internal (not datasource / not provisioning / not stack).

---

## 6. Beast anchor preservation

```
PRE  /control-postgres-beast StartedAt=2026-04-27T00:13:57.800746541Z health=healthy restarts=0
PRE  /control-garage-beast   StartedAt=2026-04-27T05:39:58.168067641Z health=healthy restarts=0
POST /control-postgres-beast StartedAt=2026-04-27T00:13:57.800746541Z health=healthy restarts=0
POST /control-garage-beast   StartedAt=2026-04-27T05:39:58.168067641Z health=healthy restarts=0
```

`diff` output: **ANCHORS-BIT-IDENTICAL**.

19+ phases of operational work / ~52 hours / 3 Phase G compose down-up cycles / Phase G compose.yaml edit + revert / Phase G 2 chowns / Phase G 2 UFW additions / Phase H read-only browser tests -- substrate untouched throughout.

---

## 7. Known limitations at ship

Per the new standing closure pattern (`feedback_phase_closure_literal_vs_spirit.md`), this section explicitly acknowledges the spirit-partial nature of Phase H closure.

**Limitation:** Dashboard 3662 ("Prometheus 2.0 Overview") is provisioned and visible in the Dashboards menu but renders all panels N/A when opened. Operators see a clearly-broken dashboard, not a silent failure. Other observability surfaces are unaffected.

**Why it ships broken:** dashboard 3662 is from the Grafana 4-5 era (~2018) and uses constructs (deprecated `singlestat` panel removed in Grafana 11.x, old variable query syntax) that Grafana 11.3.0's auto-migration cannot fix. We selected the dashboard at Phase E based on community popularity without validating Grafana 11 compatibility -- a Phase E preflight gap noted now and folded into the v0.2 hardening pass.

**Operational impact:** minimal. Node Exporter Full is the primary observability surface for host/service health. Prometheus self-monitoring (the role 3662 was meant to fill) is available via Prometheus's own UI at `http://192.168.1.40:9090/targets` and `http://192.168.1.40:9090/graph` -- canonical sources, more complete than the dashboard would have been anyway.

---

## 8. P5 carryover citation by reference

**P5 task:** Replace dashboard 3662 with a Grafana-11-compatible Prometheus self-monitoring dashboard.

**Candidate replacements for v0.2 evaluation** (per `paco_response_h1_phase_h_path_a_approved.md`):

1. Grafana dashboard **15489** -- "Prometheus 2.0 Stats" (newer, actively maintained)
2. Grafana dashboard **3681** -- "Prometheus2.0 by FUSAKLA" (alternative format)
3. **Hand-rolled minimal** -- 3-4 panels (uptime + total series + scrape duration + targets up/down) using Grafana 11's modern `stat` + `timeseries` panel types

**Validation procedure for v0.2:**
- Pull each candidate JSON, verify no deprecated panel types (`grep -i singlestat`)
- Provision against current Prometheus datasource + verify variable resolution + verify panel render in Grafana 11 sandbox before swapping into production
- If hand-rolled: build in Grafana UI, export JSON, commit to provisioning

**v0.2 hardening pass grouping** (5 items collected from H1 Phases D-G + this Phase H):
1. Goliath UFW enable (Phase D P5)
2. KaliPi UFW install + enable (Phase D P5)
3. grafana-data subdirs ownership cleanup -- `dashboards` root:root, `plugins` 472:root from Phase G ESC #2/#3 cycle (Phase G P5)
4. Grafana admin password rotation helper script wrapping the 4-step rotation flow (Phase G P5)
5. **Dashboard 3662 replacement** (this Phase H P5)

One grouped pass at v0.2 hardening time addresses all 5.

---

## 9. Inline-fix rejection rationale (per standing pattern requirement)

The standing closure pattern requires explicit accounting of which 5 conditions held + which made inline-fix the wrong call.

**Condition verification for this case:**

1. **Literal gates met as authored:** PASS. Gate 4 wording is verbatim "Dashboards render with live data from at least one node_exporter target." Node Exporter Full satisfies this exactly. No creative re-reading.

2. **Failure is contained + visible:** PASS. Operator opens dashboard 3662, sees universal N/A + warning triangles + dead panel literal text. Loud failure mode, bounded to one dashboard. No silent compromise.

3. **No substrate impact:** PASS. B2b + Garage anchors bit-identical. obs-prometheus + obs-grafana both healthy. Datasource + 7/7 scrape targets unaffected. UFW unchanged. No security surface change.

4. **Inline-fix carries non-trivial risk:** PASS. Path B (inline-replace dashboard 3662) requires evaluating 3 candidate JSONs, validating each against Grafana 11 + our datasource UID + variable schemas, picking one, swapping in provisioning, restarting compose, re-running CEO browser test. If the chosen candidate also has Grafana 11 issues -> ESC #2 chain. Real risk, not handwaving.

5. **P5 scope is appropriate:** PASS. Dashboard replacement is a v0.2 hardening task -- explicitly research + pick maintained alternative + validate against Grafana 11 first. Not a build-phase task; doing it inline at Phase H close has lower expected value than batching with the other 4 hardening items.

**All 5 conditions hold. Path A (close + P5) is the standing-pattern default. Inline-fix (Path B) was the wrong call here.**

---

## 10. Spec amendment

One-line cross-reference added to `tasks/H1_observability.md` Phase E.6 (Grafana dashboard provisioning section) per standing closure pattern requirement:

```
Note: Dashboard 3662 (Prometheus 2.0 Overview) renders all panels N/A under Grafana 11.x as of H1 ship. P5 carryover for v0.2 replacement; see Phase H paco_review + feedback_phase_closure_literal_vs_spirit.md.
```

Future readers (PD or Paco) opening the spec see the limitation is known + tracked, not unintentional.

---

## 11. Standing rule banked this phase

`docs/feedback_phase_closure_literal_vs_spirit.md` (Paco-authored at commit `0326903`, 5,596 bytes, md5 `915fb68fec8b53a94fdafc9429d6534d`).

Fourth memory file in the standing-rules registry, joining:
1. `feedback_directive_command_syntax_correction_pd_authority.md` (5-guardrail rule + 2A carve-out)
2. `feedback_paco_review_doc_per_step.md` (per-step review)
3. `feedback_paco_pd_handoff_protocol.md` (handoff protocol + bidirectional one-liner)
4. `feedback_phase_closure_literal_vs_spirit.md` (this phase's banking -- closure pattern for literal-PASS + spirit-partial)

---

## 12. Cross-references

**Predecessor doc chain (Phase H):**
- `paco_response_h1_phase_g_confirm_phase_h_go.md` (commit `d3d8ced`)
- `paco_request_h1_phase_h_prometheus_dashboard_fail.md` (PD ESC #1 of Phase H)
- `paco_response_h1_phase_h_path_a_approved.md` (commit `0326903`)
- `feedback_phase_closure_literal_vs_spirit.md` (banked at commit `0326903`)
- (this) `paco_review_h1_phase_h_grafana_smoke.md` (Phase H close-out review)

**Standing rules invoked:**
- New standing closure pattern (`feedback_phase_closure_literal_vs_spirit.md`) -- this is the first application
- Spec or no action: PD did not improvise any state changes throughout Phase H
- B2b + Garage anchor preservation invariant: holding through 19+ phases
- Bidirectional one-liner format spec on handoffs (the paired handoff file follows it)
- Secrets discipline: grafana-admin.pw value never surfaces in this review (CEO interactively typed it; PD never sees it)

---

## 13. No credentials touched

Phase H was read-only browser testing. No mutation of grafana-admin.pw or any credential file. Admin password value entered interactively by CEO into browser; never appears in PD logs, transcripts, or this review. No REDACT directive applies.

---

## 14. Status

**PHASE H CLOSED -- 4/4 LITERAL PASS** under the new standing closure pattern. One known limitation at ship documented (dashboard 3662) + P5 carryover banked + standing closure rule applied for first time + spec amendment cross-reference added.

All Phase H acceptance conditions met:
- Gates 1-4: literal PASS per spec wording
- Standing gate: B2b + Garage anchors bit-identical pre/post
- 5 standing-pattern conditions verified satisfied
- Required documentation elements (Known limitations / P5 by reference / inline-fix rationale / spec amendment) all present

Ready for Phase I (restart safety + ship report per spec section 13) GO authorization.

-- PD
