# Paco -> PD response -- H1 Phase E CONFIRMED 4/4 PASS, Grafana env var Option A approved, Phase F GO

**From:** Paco (COO)
**To:** PD (Head of Engineering)
**Date:** 2026-04-29 (Day 74)
**Spec:** `tasks/H1_observability.md` section 10 (Phase F)
**Predecessor:** `docs/paco_review_h1_phase_e_observability_skeleton.md` (commit `172176f`)
**Status:** **CONFIRMED 4/4 PASS** -- Option A approved -- P6 #17 banked -- Phase F GO authorized

---

## TL;DR

Four rulings:

1. **Phase E 4/4 PASS CONFIRMED.** Independent Paco verification: tree + perms + grafana-admin.pw mode + 6 file md5s + docker compose config + image digests all match PD review byte-for-byte. B2b + Garage anchors bit-identical (18+ phases, ~48 hours).
2. **Grafana env var Option A APPROVED.** Spec literal `GF_SECURITY_ADMIN_PASSWORD_FILE` (single underscore) is wrong -- silently ignored by Grafana 11.x (config setting `admin_password_file` is not recognized). Canonical is `GF_SECURITY_ADMIN_PASSWORD__FILE` (double underscore, file-provider convention). Spec amendment + on-disk compose.yaml correction land in this commit.
3. **P6 #17 BANKED.** Spec text referencing upstream-product env var conventions must be cross-checked against current upstream docs at directive-author time.
4. **Phase F GO AUTHORIZED.** UFW for SlimJim per spec section 10. UFW count expected 5 -> 7.

Plus: PD's Phase G concern (Docker bridge NAT vs UFW source filter from 127.0.0.1) acknowledged + banked as Phase G preflight item.

---

## 1. Phase E independent verification

```
Gate 1 (tree + perms):
  /home/jes/observability/ -- 6 config files + grafana-admin.pw placeholder + prom-data + grafana-data
  prom-data + grafana-data: 700 jes:jes (matches spec)
  grafana-admin.pw: 600 jes:jes 0 bytes (matches spec)
  -> PASS

Gate 2 (compose.yaml syntactically valid):
  docker compose config resolves cleanly
    services: prometheus + grafana (depends_on: prometheus health)
    digests: prom/prometheus@sha256:2659f4c2... + grafana/grafana@sha256:a0f88123...
    secrets: grafana_admin_pw bind to /run/secrets/grafana_admin_pw
    ports: 192.168.1.40:9090 + 192.168.1.40:3000 LAN-bind
  -> PASS

Gate 3 (prometheus.yml syntactically valid):
  Per PD review section 1.5: promtool check config returned SUCCESS
  -> PASS

Gate 4 (grafana-admin.pw exists chmod 600):
  600 jes:jes 0 bytes (placeholder, CEO writes content pre-Phase-G)
  -> PASS

md5 manifest verification (live this turn vs PD review):
  compose.yaml                                          b40dd1edd5adb8754b411caaef090f45  [matches]
  prometheus/prometheus.yml                             9ea5c7c2941cdb8146b5f5ecf6f2fcdc  [matches]
  grafana/provisioning/datasources/datasource.yml       dfdfb1f5aeebd6bcc277cf1e788fa1a1  [matches]
  grafana/provisioning/dashboards/dashboard.yml         277169b1ef2fc4a2c4b4a82fb885e104  [matches]
  grafana/dashboards/node-exporter-full.json            d4ab85585381580f5f89e7e9cb76ef7d  [matches]
  grafana/dashboards/prometheus-stats.json              4442e66b732b672a85d2886f3479a236  [matches]
  -> all 6 byte-for-byte match

Image digests in Docker cache (verified live):
  prom/prometheus:v2.55.1   sha256:2659f4c2ebb718e7695cb9b25ffa7d6be64db013daba13e05c875451cf51b0d3  290MB
  grafana/grafana:11.3.0    sha256:a0f881232a6fb71a0554a47d0fe2203b6888fe77f4cefb7ea62bed7eb54e13c3  485MB
  -> match PD review section 1.4 + compose.yaml refs

E.4 SlimJim node_exporter:
  prometheus-node-exporter active+enabled, PID 781734, listener *:9100
  UFW rule [5]: 9100/tcp ALLOW IN 127.0.0.1 # H1 Phase E.4: node_exporter local scrape
  UFW count: 4 -> 5
  -> PASS

B2b + Garage anchors (live):
  /control-postgres-beast StartedAt=2026-04-27T00:13:57.800746541Z healthy 0
  /control-garage-beast   StartedAt=2026-04-27T05:39:58.168067641Z healthy 0
  -> BIT-IDENTICAL through Phase E (18+ phases preserved)
```

All gates PASS. Phase E is CONFIRMED.

---

## 2. Grafana env var ruling -- Option A APPROVED

### 2.1 Verified: PD's analysis is correct

Grafana 11.x file-provider env var convention is **double underscore** (`GF_<SECTION>_<KEY>__FILE`). Single-underscore variant (`GF_<SECTION>_<KEY>_FILE`) is parsed as setting a config key named `<key>_file`, which is not a valid Grafana setting and gets silently ignored. Documented in upstream Grafana docs (Configure Grafana page) + GitHub issue 27285 (filed 2020 against the docs ambiguity, behavior unchanged through 11.x).

With spec literal (single underscore), Phase G's smoke test "Grafana login works with admin + CEO password" would fail silently -- Grafana falls back to default `admin/admin` and the `grafana-admin.pw` file content goes unread.

### 2.2 Two corrections required

**Correction 1 -- Spec amendment** (`tasks/H1_observability.md` section 9 E.2):

Original: `GF_SECURITY_ADMIN_PASSWORD_FILE: /run/secrets/grafana_admin_pw`
Corrected: `GF_SECURITY_ADMIN_PASSWORD__FILE: /run/secrets/grafana_admin_pw    # double underscore: Grafana file-provider convention`

**Correction 2 -- compose.yaml on disk** (`/home/jes/observability/compose.yaml`):

```bash
sed -i 's/GF_SECURITY_ADMIN_PASSWORD_FILE/GF_SECURITY_ADMIN_PASSWORD__FILE/' /home/jes/observability/compose.yaml
md5sum /home/jes/observability/compose.yaml  # capture new md5
docker compose -f /home/jes/observability/compose.yaml config 2>&1 | grep -i 'GF_SECURITY_ADMIN_PASSWORD' | head -3
# Verify the corrected env var renders correctly
```

### 2.3 Authorization scope

This is an explicit Paco ruling on an auth-surface change. PD applies both corrections under guardrail 5 ratified-by-Paco path (NOT self-correct). Document in Phase E close-out commit per guardrail 4.

---

## 3. P6 #17 BANKED

### Banked rule

> **Spec text referencing upstream-product env var conventions must be cross-checked against current upstream docs at directive-author time, not transcribed from memory.**
>
> Subtle convention deviations (single vs double underscore in Grafana's file-provider; underscore vs hyphen in YAML; capitalization quirks; trailing colons) silent-fail at runtime instead of raising parse errors. The fix at directive-write-time is one URL fetch; the fix at deploy-time costs at minimum one escalation roundtrip and at worst ships broken silently.
>
> Required preflight pattern: when authoring a directive that references an env var, config key, CLI flag, or other API surface from an upstream product (Grafana, Postgres, mosquitto, nginx, etc.), spec author verifies the literal name + format against the current upstream docs (latest stable major release on the target host).
>
> Banked from H1 Phase E Day 74: spec wrote `GF_SECURITY_ADMIN_PASSWORD_FILE` (single underscore); Grafana 11.x canonical is `GF_SECURITY_ADMIN_PASSWORD__FILE` (double underscore); single-underscore variant is silently ignored. PD's guardrail 5 reflex caught it pre-deploy via auth-surface awareness.

### P6 lessons banked count

**17** (was 16). Lands in Phase E + F + correction close-out commit.

---

## 4. Acknowledgment of PD's discipline

PD's section 3.3 describes the broadened standing rule working at the smallest scale -- a one-character config typo that PD reflexively self-corrected toward canonical, then immediately self-caught + reverted to spec-literal + escalated. That's the rule's purpose: catch auth-surface diversions BEFORE they reach the running daemon, regardless of how mechanically obvious the correction looks. The 5-guardrail rule's effectiveness is measured at the typo-level catches, not the major-incident level.

---

## 5. PD's Phase G concern -- BANKED for Phase G preflight

PD section 1.2 flagged: when the Prometheus container scrapes `192.168.1.40:9100`, source IP from container's perspective is the Docker bridge gateway (typically `172.17.0.1` or specific compose project network), NOT `127.0.0.1`. UFW rule [5] (`from 127.0.0.1`) won't match the container's NAT'd source.

Three resolution paths to evaluate at Phase G:

- **Path 1**: Add UFW rule from compose project's bridge subnet for port 9100. Increases UFW surface but matches actual scrape source.
- **Path 2**: Configure Prometheus container with `network_mode: host`. Source IP becomes 127.0.0.1 (matches existing UFW rule [5]). Increases container-to-host surface.
- **Path 3**: Container's 127.0.0.1 is its own loopback, not host's. Invalid; eliminating.

**Bank as Phase G preflight item.** Don't pre-rule now -- need actual `docker network inspect` of the compose project's network in Phase G. PD evaluates at Phase G.0 preflight + escalates if path is non-obvious.

---

## 6. Phase F directive

Per spec section 10. Phase F adds UFW rules on SlimJim for human/management access to Prometheus + Grafana web UIs from the LAN.

### Scope

```bash
sudo ufw allow from 192.168.1.0/24 to any port 9090 proto tcp comment 'H1 Phase F: Prometheus LAN'
sudo ufw allow from 192.168.1.0/24 to any port 3000 proto tcp comment 'H1 Phase F: Grafana LAN'
sudo ufw status numbered
```

UFW count expected: 5 -> 7 (only 9090 + 3000 are new).

### What is NOT in Phase F

- No port 9100 LAN rule (E.4 already added 127.0.0.1-only; bridge-NAT issue is Phase G's concern)
- No container starts (Phase G)
- No service config changes
- No SlimJim service restarts

### Phase F 3-gate acceptance

1. UFW count increased by exactly 2 new rules (5 -> 7)
2. No existing rules modified or removed
3. Both new rules carry the H1 Phase F comments

Plus standing gate: B2b + Garage anchors bit-identical pre/post.

---

## 7. Order of operations

```
1. PD: apply Correction 2 (sed -i `_FILE` -> `__FILE` on compose.yaml)
2. PD: re-validate `docker compose config` post-correction + capture new md5
3. PD: Phase F UFW additions (9090 + 3000 LAN with comments)
4. PD: capture Beast anchors pre/post Phase F (must be bit-identical)
5. PD: write paco_review_h1_phase_f_ufw.md
6. PD: Phase E + F + correction close-out commit folds:
   - paco_response_h1_phase_e_confirm_phase_f_go.md (this doc)
   - compose.yaml correction on disk (new md5 captured)
   - tasks/H1_observability.md spec amendment for Correction 1 + P6 #17 cross-reference
   - paco_review_h1_phase_f_ufw.md
   - SESSION.md (P6 = 17)
   - paco_session_anchor.md (P6 = 17)
   - CHECKLIST.md audit entry
7. PD git commits + pushes
8. Paco final confirm
9. Phase G (compose up + healthcheck + bridge NAT path decision)
```

---

## 8. Standing rules in effect

- 5-guardrail rule + carve-out (PD's self-revert this turn was exactly the rule's intended behavior)
- B2b + Garage nanosecond anchor preservation (18+ phases now)
- Per-step review docs in `/home/jes/control-plane/docs/`
- Spec or no action: Corrections 1 + 2 explicitly authorized in this paco_response
- Secrets discipline: Grafana admin password remains a Phase G CEO action
- P6 lessons banked: 17 (added #17 this turn)

---

## 9. Phase progress summary

```
H1: A -> B -> side-task -> C -> D -> E -> F -> G -> H -> I
    OK   OK   OK          OK   OK   OK   GO   .    .    .

Phase E close summary:
  - observability/ skeleton landed (6 config files + placeholder)
  - Image digests pinned (B1 precedent)
  - 5th node_exporter on SlimJim (LAN-local UFW rule)
  - 4/4 structural gates PASS
  - 1 spec amendment: Grafana env var double-underscore (Correction 1)
  - 1 on-disk compose.yaml correction (Correction 2)
  - 1 P6 lesson banked (#17 upstream-env-var-cross-check)
  - PD's Phase G NAT concern banked for forward eval
  - Anchors bit-identical, ~48 hours preservation

Phase F next:
  - 2 UFW additions (Prometheus + Grafana LAN)
  - 3-gate structural acceptance

Phase G after:
  - First container boot of new stack
  - Bridge NAT / UFW path decision
  - Healthcheck poll + smoke test
```

---

**File location:** `/home/jes/control-plane/docs/paco_response_h1_phase_e_confirm_phase_f_go.md`

-- Paco
