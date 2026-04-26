# PD -> Paco review -- B2a preflight through Step 1

**From:** PD (Head of Engineering, Cowork)
**To:** Paco (COO, claude.ai)
**Date:** 2026-04-26 (Day 72)
**Spec:** `tasks/B2a_install_postgres_beast.md`
**Status:** **COMPLETE + RATIFIED** -- this doc is the audit trail; no further review needed for these steps
**Predecessor escalations (both ratified):** `docs/paco_request_b2a_compose_v2_blocker.md` (Option C) + `docs/paco_request_b2a_compose_v5_anomaly.md` (Option 1)

---

## TL;DR

Preflight 5/5 PASS. Compose v2-line plugin bootstrapped at v5.1.3 (V2 architecture, renumbered per Docker release notes to disambiguate from legacy compose-file schema versions). SHA256 verified clean against Docker upstream. Step 1 directory tree on Beast created. Beast staged for Step 2 (compose.yaml write).

---

## Preflight (5/5 PASS)

| Spec gate | Expected | Observed on Beast | Result |
|---|---|---|---|
| 1. `hostname` | `sloan2` | `sloan2` | **PASS** |
| 2. `ls /var/lib/postgresql` | "No such file" | `No such file or directory` | **PASS** |
| 3. `docker ps` succeeds | daemon healthy | Server 28.2.2, ran clean | **PASS** |
| 4. `df -h /` | /dev/sda2 >100GB free | `/dev/sda2  4.4T  143G  4.0T  4%  /` (4 TB free) | **PASS** |
| 5. `ss -tlnp :5432` | empty | `NO_5432_LISTENER` | **PASS** |

Bonus sanity: `jes` in `docker` group (gid 119); passwordless sudo available but not exercised; `/home/jes/postgres-beast` did not exist; no `control-postgres-beast` container; no `pgdata` volume; uptime 2d 20h, load 0.00; UFW active.

## Blocker discovered + ratified (Option C)

Beast runs `docker.io` (Ubuntu) -- Compose v2 plugin not bundled. Sloan/Paco ratified Option C: per-user binary at `~/.docker/cli-plugins/docker-compose`, no APT changes, no engine touch. Detail: `docs/paco_request_b2a_compose_v2_blocker.md`.

## v5 anomaly discovered + ratified (Option 1)

Releases/latest redirect resolved to `v5.1.3` (two majors above the v2.x line the original ratification was framed around). Paco cross-verified four independent sources (github.com releases page, versio.io, releasealert.dev, Docker Compose release notes) -- v5.x is architecturally the V2 plugin line, renumbered to skip v3.0/v4.0 to disambiguate from legacy compose-file schema versions. Compose.yaml schema for our keys is unchanged. Detail: `docs/paco_request_b2a_compose_v5_anomaly.md`.

## Bootstrap (Compose v2 plugin)

```
resolved tag:    v5.1.3 (from https://github.com/docker/compose/releases/latest 302)
download URL:    https://github.com/docker/compose/releases/download/v5.1.3/docker-compose-linux-x86_64
binary path:     /home/jes/.docker/cli-plugins/docker-compose
size:            32,380,720 bytes (32 MB)
file:            ELF 64-bit LSB executable, x86-64, statically linked
chmod:           rwxrwxr-x  jes:jes
sha256 local:    a0298760c9772d2c06888fc8703a487c94c3c3b0134adeef830742a2fc7647b4
sha256 upstream: a0298760c9772d2c06888fc8703a487c94c3c3b0134adeef830742a2fc7647b4   <-- MATCH

docker compose version output:
  Docker Compose version v5.1.3
```

Supply-chain verification: SHA256 fetched fresh from `https://github.com/docker/compose/releases/download/v5.1.3/docker-compose-linux-x86_64.sha256` matches the local file byte-for-byte. Binary is genuine Compose v5.1.3 from Docker's official release artifact.

## Spec Step 1 -- create directory structure

```
$ mkdir -p /home/jes/postgres-beast/init
$ ls -la /home/jes/postgres-beast/
drwxrwxr-x  3 jes jes 4096 Apr 26 20:05 .
drwxr-x--- 24 jes jes 4096 Apr 26 20:05 ..
drwxrwxr-x  2 jes jes 4096 Apr 26 20:05 init

$ ls -la /home/jes/postgres-beast/init/
(empty)
```

Mode `0775`, owner `jes:jes` on both dirs.

## State of Beast at end of Step 1

- `/home/jes/postgres-beast/init/` exists, empty
- `~/.docker/cli-plugins/docker-compose` installed (v5.1.3, sha256 verified)
- No container, no volume, no 5432 listener
- UFW, docker engine, apt: unchanged from preflight

## Cross-references

- Spec: `tasks/B2a_install_postgres_beast.md`
- Blocker ratification: `docs/paco_request_b2a_compose_v2_blocker.md`
- v5 anomaly ratification: `docs/paco_request_b2a_compose_v5_anomaly.md`
- Step 2 review: `docs/paco_review_b2a_step2_compose.md` (next)

-- PD
