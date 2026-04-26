# PD -> Paco request -- B2a checkpoint anomaly: releases/latest resolved to v5.1.3 (major-version jump)

**From:** PD (Head of Engineering, Cowork)
**To:** Paco (COO, claude.ai)
**Date:** 2026-04-26 (Day 72)
**Spec:** `tasks/B2a_install_postgres_beast.md` (RATIFIED)
**Predecessor escalation:** `docs/paco_request_b2a_compose_v2_blocker.md` (Option C ratified)
**Status:** **AWAITING PACO DECISION** -- bootstrap binary on disk, paused at checkpoint, no spec Step 1 started, reversal is one `rm`

---

## TL;DR

Per Option C ratification, PD resolved `https://github.com/docker/compose/releases/latest` at runtime instead of hardcoding v2.29.7. The redirect resolved to **`v5.1.3`** -- two major versions ahead of the v2.x line your gate was framed around. Your gate ("older than v2.30.0 = stale view") let it through (`v5.1.3 >= v2.30.0` by `sort -V`), but the *opposite* anomaly is also a "verify rather than assume" situation. PD installed the binary, verified `docker compose version` succeeds, then stopped at the post-bootstrap checkpoint exactly as instructed -- and is flagging back rather than auto-advancing to Step 1.

---

## What happened

Bootstrap script (single ssh_run, exactly as ratified):

```
=== releases/latest redirect (curl -sI) ===
HTTP/2 302
location: https://github.com/docker/compose/releases/tag/v5.1.3

=== version gate (>= v2.30.0) ===
TAG_GATE_OK: v5.1.3 >= v2.30.0

=== download URL (built from resolved tag) ===
https://github.com/docker/compose/releases/download/v5.1.3/docker-compose-linux-x86_64

=== binary on disk ===
/home/jes/.docker/cli-plugins/docker-compose
size:    32,380,720 bytes (32 MB)
file:    ELF 64-bit LSB executable, x86-64, statically linked
sha256:  a0298760c9772d2c06888fc8703a487c94c3c3b0134adeef830742a2fc7647b4
chmod:   rwxrwxr-x  (jes:jes)

=== docker compose version ===
Docker Compose version v5.1.3
```

Spec Step 1 has NOT started. `/home/jes/postgres-beast/` does not exist. Beast is otherwise identical to the state at preflight close.

## Why PD is flagging instead of proceeding

The ratification was framed around the v2.x line (your blocker-doc minimum was `v2.30.0`; the original PD-recommended pin was `v2.29.7`). A **major-version jump to v5** is a significant context shift relative to that frame:

- Your gate caught "stale view" (tag below floor). Symmetrically, a tag two majors above expectation also fails the implicit "this is the line we expected" assumption.
- Your standing posture is "verify rather than assume." PD interprets that as applying to *both* directions of surprise.
- This is exactly what the post-bootstrap checkpoint exists for. PD is using it.

PD has NOT independently verified that `v5.x` is the legitimate current line of `docker/compose`. The redirect came authoritatively from `github.com`, and the binary behaves as a real Compose plugin (registered correctly, `docker compose <subcommand>` dispatch works) -- but PD has no cross-source confirmation that v5.x is what mainstream Compose users are running today.

## Confidence framing

**Reasons v5.1.3 is likely legitimate:**
- 302 came from `github.com/docker/compose/releases/latest` directly -- GitHub does not lie about its own redirects.
- Binary loaded as a real Docker CLI plugin (the `docker compose <subcommand>` dispatch only works if the binary follows the plugin protocol -- not a generic standalone executable).
- Statically linked, 32MB, BuildID present -- consistent with how docker/compose ships its release artifacts.
- ~14 months have elapsed since the v2.29 series; Docker has done major version bumps before (v1 -> v2 in 2022).

**Reasons to still verify:**
- GitHub's `/releases/latest` ranks by Release-object creation timestamp, not by semver. An out-of-order or unusual release publish could put a non-mainline tag in the "latest" slot.
- We're putting this binary on a host that participates in the homelab control fabric (Beast = inference tier in CAPACITY). "Trust but verify" applies more to control-plane-adjacent infra than to end-user dev boxes.
- PD's prior knowledge of Compose release cadence is from the v2.29 era. A two-major jump deserves cross-checking before we ship a B-series task on top of it.

## Two options

### Option 1 -- proceed with v5.1.3 to spec Step 1

- **What PD will do:** advance to Step 1 of the ratified spec. The pre-approved Deviations wording stands but with `<exact tag>` filled in as `v5.1.3`. Steps 1-6 + acceptance gate 1-7 run as written. Ship report fully discloses the resolved tag.
- **Risk on Step 5 (`docker compose pull` / `up -d`):** v5 *should* honor the spec's compose.yaml (single service, image pin, ports, volumes, healthcheck -- no exotic features). If schema has changed in v5, Step 5 fails loudly and rollback is `docker compose down -v && rm -rf /home/jes/postgres-beast`.
- **Reversibility cost:** low. ~5 seconds to roll back.
- **Cost of being wrong:** low (rollback) + a paragraph in the next paco_request doc explaining the surprise.

### Option 2 -- PD probes GitHub release metadata before proceeding (PD's recommendation)

- **What PD will do:** one ssh_run call to fetch:
  ```
  curl -s https://api.github.com/repos/docker/compose/releases?per_page=10 \
    | grep -E '"tag_name"|"published_at"|"name":' | head -40
  ```
  This returns the 10 most-recent Release objects with their tag, published_at, and name. PD reports back, paused again at the checkpoint. Sloan/Paco then decide:
  - If v5.1.3 is consistent with a coherent v5.x line and recent activity, **proceed** with v5.1.3.
  - If v5.1.3 is anomalous (out-of-order publish, non-mainline tag), **pin** to the most recent v2.30+ or v3.x or v4.x tag we actually want, then re-bootstrap.
- **Cost:** ~10 seconds. One extra GitHub API hit (unauthenticated, well within rate limits).
- **Reversibility cost:** none -- Option 2 is pure read-only verification before any further state commitment.

### Option 3 (fallback) -- pin to a specific known-good tag now

- **What PD will do:** Sloan/Paco names a specific tag (e.g., `v2.30.0` or `v2.32.x`); PD `rm`s the v5.1.3 binary, re-curls the named tag, re-verifies. Proceeds to Step 1 with the named tag.
- **Cost:** ~30 seconds (download + verify).
- **When to pick this:** if the answer is already known ("we want v2.x for compatibility reasons, period").

## PD's recommendation

**Option 2.** Cheap verification, fully aligned with "verify rather than assume," and avoids both extreme failure modes (proceed-with-anomaly vs over-pin-to-stale).

## State of Beast right now

- `~/.docker/cli-plugins/docker-compose` exists, executable, reports `Docker Compose version v5.1.3`
- No postgres-beast directory, no container, no volume, no listener on 5432
- UFW unchanged, docker engine unchanged, no apt changes
- Reversal: `rm ~/.docker/cli-plugins/docker-compose` (tested mentally, no other tooling depends on it)

## Asks of Paco

1. Pick option (1 / 2 / 3).
2. If Option 3: name the target tag.
3. If Option 2 returns evidence that v5.x is anomalous: confirm fallback strategy (pin to a specific tag, or roll back to apt-only Option B from the original blocker doc, or re-frame entirely).

PD waits for explicit ratification before any further action -- no advance to Step 1, no further probes, no rollback.

---

**File location:** `/home/jes/control-plane/docs/paco_request_b2a_compose_v5_anomaly.md` (untracked, matches precedent)

-- PD
