# paco_request_h1_phase_h_prometheus_dashboard_fail

**Spec:** H1 -- Phase H Grafana smoke + LAN smoke from CK + CEO browser test (`tasks/H1_observability.md` section 12)
**Step:** Phase H -- post CEO browser test results
**Status:** ESCALATION. Phase H 4-gate criteria literally PASS but one provisioned dashboard does not render. Spec is silent on "one of N provisioned dashboards fails but at-least-one criterion satisfied" -- Paco architectural ruling needed on whether Phase H closes 4/4 + P5 or treats as Gate 4 partial.
**Predecessor:** `docs/paco_response_h1_phase_g_confirm_phase_h_go.md` (commit `d3d8ced`)
**Author:** PD
**Date:** 2026-04-29 (Day 74)
**Target host:** SlimJim (`192.168.1.40`) -- obs-grafana container

---

## TL;DR

CEO browser test results:

- **Node Exporter Full** (dashboard 1860): **PASS** end-to-end. Login succeeded, dashboard rendered with live data (CPU 1.7% / RAM 4.8% / disk 25.3% / network kb/s / uptime 6.3 days for SlimJim instance `192.168.1.40:9100`). Datasource Prometheus is healthy + connected; provisioning works; dashboard JSON renders cleanly.
- **Prometheus 2.0 Overview** (dashboard 3662): **FAIL**. All panels show N/A. Variable dropdowns (`job`, `instance`) show warning triangles -- variable queries can't resolve. One panel shows literal text `"Panel plugin has no panel component"` -- deprecated panel type (`singlestat`) removed in Grafana 11.

The failure is isolated to dashboard 3662, NOT the datasource or provisioning. Root cause: dashboard 3662 is from Grafana 4-5 era (~2018), uses deprecated panel types + old variable query syntax, and Grafana 11.3.0's auto-migration cannot fix it.

Gate 4 wording is literally "Dashboards render with live data from **at least one** node_exporter target" -- Node Exporter Full satisfies this exactly. Strict spec reading: 4/4 PASS. Spirit-of-test reading: partial (provisioned dashboard inventory has one broken member).

B2b + Garage anchors bit-identical pre/post entire Phase H interaction (read-only browser tests). Substrate undisturbed.

---

## 1. Phase H 4-gate scorecard (strict spec reading)

| Gate | Description | Status |
|------|-------------|--------|
| 1 | Grafana web HTTP 200 + login page renders | PASS (CEO confirmed) |
| 2 | CEO login succeeds with admin + grafana-admin.pw | PASS (CEO confirmed) |
| 3 | Both provisioned dashboards visible in Dashboards menu | PASS (CEO confirmed both visible) |
| 4 | Dashboards render with live data from at least one node_exporter target | PASS (Node Exporter Full = SlimJim 192.168.1.40:9100, fully populated) |

Plus standing gate: B2b + Garage anchors bit-identical pre/post -- PASS (read-only Phase, substrate untouched).

Literal 4/4 PASS.

## 2. Spirit-of-test reading

The Phase H spec's underlying intent appears to be "both provisioned dashboards (1860 + 3662) work end-to-end with live Prometheus data." Under that lens, dashboard 3662's universal N/A + variable failure + dead panel constitutes a partial failure even though Gate 4's literal at-least-one criterion is satisfied.

The gap: spec wording was permissive ("at least one"); spirit was inclusive (both). Spec is silent on the partial-failure case.

---

## 3. Failure evidence -- dashboard 3662

CEO screenshot evidence from browser test:

- All panels show universal `N/A`
- Variable dropdowns: `job [x x x]` warning triangle, `instance [All x x]` warning triangle -- variable queries failing to resolve
- One panel shows literal text: `"Panel plugin has no panel component"` -- deprecated panel type (singlestat removed in Grafana 11.x)
- Variable resolution failure cascades: panels using `$job` or `$instance` get no values, queries return empty, panels render N/A
- No actual query errors visible in panel info icons (queries technically execute, just produce no result given empty variables)

## 4. Datasource is healthy (Node Exporter Full proves it)

Node Exporter Full dashboard (1860) is rendering with live data from the same Prometheus datasource. Specifically:

- Datasource dropdown: `Prometheus` (resolved cleanly)
- Job: `node` (resolved)
- Nodename: `sloan1` (resolved)
- Instance: `192.168.1.40:9100` (resolved)
- Time range: Last 24 hours (rendering live data)
- Live values: CPU 1.7% / Memory 4.8% / Root FS 25.3% / 31 GiB RAM / 271 GiB disk / Uptime 6.3 days
- Time-series panels (CPU Basic, Memory Basic, Network Traffic Basic, Disk Space Used Basic): all rendering live data with proper timeline

This confirms:
- Provisioning files mounted + parsed correctly
- Datasource UID resolution working
- Grafana -> Prometheus container-to-container connectivity working
- Prometheus has data + Prometheus is serving queries correctly
- Dashboard 1860 is Grafana-11-compatible

The failure is specifically dashboard 3662, not the stack.

---

## 5. Resolution paths

### 5.1 Path A -- Close Phase H 4/4 + P5 carryover

Close Phase H per literal Gate 4 criteria. Document dashboard 3662 failure as P5 carryover for v0.2: "Replace deprecated Prometheus 2.0 Overview (3662) with Grafana-11-compatible alternative."

**Pros:**
- Literal spec criteria met
- Lowest cognitive overhead, fastest path to Phase I
- Honest about what works (Node Exporter Full is the primary observability surface; Prometheus self-monitoring is supplementary)
- Matches established P5 pattern

**Cons:**
- Provisioned dashboard inventory has known-broken member shipping at H1 close
- Spirit-of-test ambiguity could create confusion at ship-report time

### 5.2 Path B -- Inline-fix dashboard 3662 before closing Phase H

Replace `prometheus-stats.json` in `/home/jes/observability/grafana/dashboards/` with either:
- A maintained alternative (e.g., dashboard 19654 "Prometheus Stats" or 14694 "Prometheus 2 Overview" -- different IDs)
- A minimal hand-built Prometheus self-monitoring dashboard (uptime + total series + up{job="prometheus"})

Then restart obs-grafana to reload provisioning, re-test browser.

**Pros:**
- Phase H closes complete (both dashboards working)
- Spirit-of-test satisfied
- Cleaner H1 ship report

**Cons:**
- File swap is operational config mutation (escalation territory; PD self-auth doesn't apply per "spec or no action")
- Adds a phase-G-class change to the close-out (compose restart, not just file change)
- Replacement dashboard may itself need validation (could trigger ESC #2 if alternative also has issues)
- Spec amendment to tasks/H1_observability.md needed (Phase E.6 dashboard list change)

### 5.3 Path C -- Drop dashboard 3662 from spec entirely

Remove `prometheus-stats.json` from provisioning. Update Phase E.6 spec to provision only Node Exporter Full. Compose restart to reload provisioning.

**Pros:**
- Cleanest spec state
- Prometheus has its own /targets endpoint at http://192.168.1.40:9090/targets for self-monitoring
- No dependency on community dashboard maintenance

**Cons:**
- Loses Prometheus self-monitoring dashboard surface entirely
- Operator workflow change (use Prometheus UI directly vs Grafana dashboard)
- Spec amendment + file removal + compose restart still needed

### 5.4 Path D -- Other (Paco-defined)

Something Paco wants to consider that PD didn't surface.

---

## 6. PD bias

**Path A.** Three reasons:

1. **Literal spec criteria met.** Phase H is structurally complete per the gate wording you authored. Re-litigating the literal criterion creates process drift.

2. **Operational reality.** Node Exporter Full IS the primary observability surface for this stack -- it shows the actual host/service health that matters operationally. Prometheus self-monitoring is supplementary diagnostic; we'd rarely reach for it during normal ops, and when we do, the Prometheus UI at /targets is the canonical source anyway.

3. **P5 carryover is correctly scoped.** Replacing 3662 with a maintained alternative is a clean v0.2 task -- explicitly research + pick a maintained dashboard, validate against Grafana 11 first, swap. Doing it inline at Phase H close has higher risk (replacement dashboard might also fail, triggering ESC chain) for marginal reward.

Path B is acceptable if Paco prioritizes spec-spirit completeness over Phase I velocity. Path C is reasonable but loses a useful dashboard surface.

---

## 7. PD has NOT done

- Modified provisioning files (no path applied)
- Restarted obs-grafana
- Captured Beast anchor post (deferred until Phase H close-out)
- Modified spec or compose state

Phase H state is currently: PD-side checks done, CEO browser test results in, awaiting Paco ruling on close path.

---

## 8. Asks of Paco

1. **Path ruling.** A (close 4/4 + P5) vs B (inline-fix 3662) vs C (drop from spec) vs D (other)?
2. **If Path B or C** -- spec amendment scope (which Phase E section, what wording).
3. **P5 carryover banking** -- if Path A, register the v0.2 task in standing P5 list with specific dashboard alternatives evaluated as starting point.
4. **Standing pattern for future phases** -- when literal gate criteria PASS but spirit-of-test partial, what's the rule? P5 by default vs ESC by default? This case sets the precedent.

---

## 9. State at this pause

### 9.1 What is true now

- obs-prometheus: Status=running, Health=healthy, Restarts=0
- obs-grafana: Status=running, Restarts=0, listening :3000
- 7/7 Prometheus targets up (unchanged from Phase G close)
- Datasource provisioning working (Prometheus, default, http://prometheus:9090)
- Dashboard provisioning working (both JSONs loaded, but 3662 fails to render)
- Beast anchors bit-identical (B2b 2026-04-27T00:13:57.800746541Z + Garage 2026-04-27T05:39:58.168067641Z)
- compose.yaml unchanged (md5 db89319cad27c091ab1675f7035d7aa3, Phase F state)
- grafana-admin.pw unchanged (600 472:472 11 bytes)
- UFW unchanged (9 rules)
- Phase H 4-gate scorecard: literal 4/4 PASS, spirit-of-test partial

### 9.2 What is unchanged since `d3d8ced`

- All observability/ files
- All container state
- All UFW rules
- All node_exporter installs
- Beast substrate

---

## 10. Cross-references

**Standing rules invoked:**
- 5-guardrail rule: this is OUTSIDE its domain (architectural / spec-interpretation decision, not mechanical correction)
- Spec or no action: PD has not improvised any state changes
- B2b + Garage anchor preservation invariant: holding
- Bidirectional one-liner format spec on handoffs (this ESC's handoff_pd_to_paco.md follows it)

**Predecessor doc chain (Phase H):**
- `paco_response_h1_phase_g_confirm_phase_h_go.md` (commit `d3d8ced`)
- `docs/handoff_paco_to_pd.md` (Day 74, cleared per protocol)
- (this) `paco_request_h1_phase_h_prometheus_dashboard_fail.md` (PD ESC #1 of Phase H)

---

## 11. Status

**AWAITING PACO RULING on:**
1. Path A (close 4/4 + P5) vs B (inline-fix) vs C (drop) vs D (other)
2. Spec amendment scope if B or C
3. P5 carryover banking if A
4. Standing pattern for literal-PASS + spirit-partial cases

PD paused. Stack running healthy. Substrate undisturbed. No further changes pending Paco's response.

-- PD
