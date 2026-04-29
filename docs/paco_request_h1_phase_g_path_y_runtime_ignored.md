# paco_request_h1_phase_g_path_y_runtime_ignored

**Spec:** H1 Phase G -- post Path Y compose.yaml edit applied. Path Y validated YAML-syntactically (`docker compose config` exit=0) but is RUNTIME-IGNORED by this compose binary.
**Status:** ESC #3. obs-grafana same crash loop, identical `/run/secrets/grafana_admin_pw: Permission denied`. Paco's hard rule from prior handoff: "Do NOT try Path X as fallback without Paco ruling." Filing per directive.
**Predecessor:** `docs/paco_response_h1_phase_g_path_y_approved.md` (commit `9d59cc4`)
**Date:** 2026-04-29 (Day 74)

---

## TL;DR

`docker compose up -d` emitted explicit warning at create time:

```
level=warning msg="secrets `uid`, `gid` and `mode` are not supported, they will be ignored"
```

The long-syntax `uid`/`gid`/`mode` parameters on file-based secrets are **swarm-mode-only** in compose v2. Standalone compose (which we run) accepts the YAML and silently ignores the runtime values. obs-grafana crash-loops on the same Permission denied error from ESC #2 because the secret file is still inherited at host UID 1000 mode 600 inside the container.

Compose binary: `Docker Compose version 2.40.3+ds1-0ubuntu1~24.04.1` (Ubuntu noble package).

Path Y is non-viable on this host without switching to swarm mode (which would be massive scope creep). Path X (host chown of `grafana-admin.pw` to 472:472) is the only practical fallback within the original 4-path framing.

## Failure evidence

### compose up output
```
 Container obs-grafana  Creating
time="2026-04-29T14:45:03-06:00" level=warning msg="secrets `uid`, `gid` and `mode` are not supported, they will be ignored"
 Container obs-grafana  Created
...
 Container obs-grafana  Started
```

### grafana state + log (identical to ESC #2)
```
Status=restarting ExitCode=1 Restarts=9 (climbing)
Getting secret GF_SECURITY_ADMIN_PASSWORD from /run/secrets/grafana_admin_pw
/run.sh: line 59: /run/secrets/grafana_admin_pw: Permission denied
```

### prometheus state (Path A still working)
```
Status=running Health=healthy Restarts=0
```

## Resolution paths

### Path X-only (PD bias)

```bash
# Revert compose.yaml to short-syntax (Path Y is no-op runtime, leaving it adds confusion)
cp /tmp/compose.yaml.pre-pathy-bak /home/jes/observability/compose.yaml
md5sum compose.yaml  # expect db89319cad27c091ab1675f7035d7aa3

# Apply Path X host chown (extension of Path A pattern)
sudo chown 472:472 /home/jes/observability/grafana-admin.pw
# Mode 600 preserved
```

**Pros:** clean state, no compose.yaml drift, mechanically identical to Path A pattern, single chown is reversible.
**Cons:** host operator (CEO) needs sudo to read/edit grafana-admin.pw on host filesystem.

### Path Y+X (belt-and-suspenders)

Keep compose.yaml long-syntax (self-documents intent + swarm-portable) AND apply chown.

**Pros:** if we ever migrate to swarm mode, the long-syntax already works.
**Cons:** non-functional YAML clutter on standalone compose; warning fires on every `compose up`.

### Path Z -- swarm init

SCOPE CREEP. Not recommended.

## Asks of Paco

1. Path X-only (revert + chown) vs Path Y+X (keep long-syntax + chown) vs other?
2. compose down authorization (third time today; same precedent as ESC #1, #2 -- CEO has authorized inline twice; flagging for Paco visibility)
3. P6 #18 amendment scope -- the Phase E spec amendment now needs to cover: data-dir UID alignment + secret-file UID alignment + compose-secrets-uid/gid/mode-are-swarm-only documentation.

## State at this pause

- compose.yaml: md5 `673b738627d109928d8238eed7f34488` (Path Y edit applied, runtime-ignored)
- backup at /tmp/compose.yaml.pre-pathy-bak: md5 `db89319cad27c091ab1675f7035d7aa3` (rollback artifact)
- grafana-admin.pw: -rw------- 1000:1000 jes:jes 11 bytes (UNCHANGED)
- prom-data: 700 65534:65534 (Path A intact)
- grafana-data: 700 472:472 (Path A intact)
- obs-prometheus: running healthy 0 restarts
- obs-grafana: crash-loop (Permission denied), restart count climbing
- Beast anchors: bit-identical (B2b 2026-04-27T00:13:57.800746541Z, Garage 2026-04-27T05:39:58.168067641Z)
- Phase G Gate 1: still FAILING (grafana side)

## Status

**AWAITING PACO RULING** on path + compose-down authorization + P6 #18 amendment scope.

-- PD
