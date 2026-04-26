# PD -> Paco request -- B2a blocker: Docker Compose v2 plugin missing on Beast

**From:** PD (Head of Engineering, Cowork)
**To:** Paco (COO, claude.ai)
**Date:** 2026-04-26 (Day 72)
**Spec:** `tasks/B2a_install_postgres_beast.md` (RATIFIED 2026-04-26)
**Status:** **AWAITING PACO DECISION** -- B2a execution paused at end of preflight, no state change on Beast

---

## TL;DR

All 5 spec preflight gates **PASS** on Beast. But the spec's literal commands (`docker compose pull`, `docker compose up -d`, etc.) require Compose v2 plugin, and Beast has **only legacy Compose v1** (`docker-compose` 1.29.2, EOL Feb 2023). Three remediation paths exist; PD recommends a per-user binary install (Option C) and is asking for explicit ratification before deviating from spec literal.

Per Sloan's standing instruction ("If anything in the spec is ambiguous or needs deviation, flag back rather than improvising") and Standing Rules operational expectation ("Caught at execution -> PD flag -> Paco revise -> re-issue"), PD has stopped at the preflight gate.

---

## Preflight results (full)

| Spec gate | Expected | Observed on Beast | Result |
|---|---|---|---|
| 1. `hostname` | `sloan2` | `sloan2` | **PASS** |
| 2. `ls /var/lib/postgresql` | "No such file" | `No such file or directory` | **PASS** |
| 3. `docker ps` succeeds | daemon healthy | Server 28.2.2, ran clean | **PASS** |
| 4. `df -h /` | /dev/sda2 >100GB free | `/dev/sda2  4.4T  143G  4.0T  4%  /` (4 TB free) | **PASS** |
| 5. `ss -tlnp :5432` | empty | `NO_5432_LISTENER` | **PASS** |

**Bonus sanity (all clean):**
- SSH user on Beast: `jes` (uid 1000); in `docker` group (gid 119) -- no sudo needed for compose commands
- `(ALL : ALL) ALL` passwordless sudo available for jes (informational; not exercised)
- `/home/jes/postgres-beast` does not exist
- No `control-postgres-beast` container, no `pgdata` volume
- Existing images on Beast: `nvcr.io/nvidia/pytorch:25.11-py3` (20.5GB), `hello-world` (10kB) -- no conflict with `pgvector/pgvector:pg16`
- Uptime 2d 20h, load 0.00 -- host idle
- UFW active (Beast's existing IoT-block ruleset present); confirms CLAUDE.md hard rule "Docker bypasses UFW. Bind to localhost in compose.yaml" remains essential -- spec already does this (`127.0.0.1:5432:5432`).

## Blocker -- Compose v2 plugin missing

```
$ docker compose version
docker: unknown command: docker compose
```

Probed deeper:

```
$ which docker-compose
/usr/bin/docker-compose
$ docker-compose --version
docker-compose version 1.29.2, build unknown      <-- legacy v1, Python, EOL Feb 2023

$ ls /usr/libexec/docker/cli-plugins/  /usr/lib/docker/cli-plugins/  ~/.docker/cli-plugins/
(all three: "No such file or directory")          <-- no Compose v2 binary anywhere

$ dpkg -l | grep -iE 'compose|docker'
ii  docker-compose          1.29.2-1                                  all
ii  docker.io               28.2.2-0ubuntu1~22.04.1                   amd64
ii  python3-docker          5.0.3-1                                   all
ii  python3-dockerpty       0.4.1-2                                   all

$ apt-cache policy docker-compose-plugin
(empty -- package not in any configured apt source)

$ ls /etc/apt/sources.list.d/ | grep -i docker
(empty -- Docker Inc's official APT repo NOT configured)
```

**Root cause:** Beast runs `docker.io` from Ubuntu's repos (NOT `docker-ce` from Docker Inc), and Ubuntu's `docker.io` package does not bundle the Compose v2 plugin. Without Docker Inc's official APT repo configured, `docker-compose-plugin` is not even an apt candidate. Compose v1 was retained from before, but it's not what the spec calls.

## Why I stopped

The spec's Step 5 ("`docker compose pull`") and Step 6 ("`docker compose ps`", "`docker compose restart`") and acceptance gate 7 ("`docker compose restart` returns container to healthy within 60s") all assume Compose v2. Improvising onto v1 (or installing v2 silently) would be a deviation. Per CLAUDE.md operating rule: "Spec or no action."

No state change has occurred on Beast. Rolling back is a no-op.

## Three remediation options (ranked least-invasive first)

### Option C -- per-user Compose v2 binary plugin (PD's recommendation)

```bash
mkdir -p ~/.docker/cli-plugins
curl -SL https://github.com/docker/compose/releases/download/v2.29.7/docker-compose-linux-x86_64 \
  -o ~/.docker/cli-plugins/docker-compose
chmod +x ~/.docker/cli-plugins/docker-compose
docker compose version    # confirm
```

- **Pros:** matches spec literal commands; ~50MB single binary; no APT changes; no sudo; fully reversible (`rm` the file); doesn't touch the engine; doesn't risk a docker.io -> docker-ce swap on next apt upgrade
- **Cons:** binary not apt-tracked (mitigation: pin a specific Compose release, e.g. v2.29.7; document in ship report; refresh on a known cadence)
- **Diff from spec:** an additive bootstrap step before Step 1; ship report "Deviations" section gets a one-line note. Steps 1-6 + acceptance gate run as written.

### Option A -- add Docker Inc's APT repo + install `docker-compose-plugin`

- **Pros:** apt-tracked
- **Cons:** mixing `docker.io` (Ubuntu) with Docker Inc's repo is unsupported. `apt upgrade` on a misconfigured pin would attempt a `docker.io` -> `docker-ce` swap on a host that's also running NVIDIA GPU drivers + Ollama in the docker group. Real risk for one binary.
- **Recommendation:** avoid.

### Option B -- substitute legacy `docker-compose` v1 throughout B2a

- **Pros:** zero install
- **Cons:** Compose v1 is EOL and unsupported. YAML compatibility *should* hold for this simple file (single service, no obscure features), but I haven't probe-tested. Spec literal deviation is non-trivial: every B2a + future B2b/B-series command would need v1/v2 case-handling, and gate 7 wording would need adjustment.
- **Recommendation:** avoid.

## What PD will do on approval

**On Option C approval (recommended):**

1. One ssh_run call: install Compose v2 binary at `~/.docker/cli-plugins/docker-compose`, chmod +x, run `docker compose version` to verify. Pause and report.
2. Proceed Steps 1-6 of spec exactly as written, one step per turn with explicit go between steps.
3. Verify acceptance gate items 1-7. Run `docker compose restart` for gate 7.
4. Write ship report at `/home/jes/postgres-beast/B2a_ship_report.md` (per spec format, all 7 gate results with command output evidence, container ID + image digest, pgdata disk usage, md5sums, deviations + reasoning, time elapsed).
5. **Add to ship report "Deviations" section:** "Compose v2 plugin (v2.29.7) installed at `~/.docker/cli-plugins/docker-compose` as bootstrap step prior to Step 1; Beast's docker.io package does not bundle v2. Approved by Paco via `docs/paco_request_b2a_compose_v2_blocker.md`. Reversal: `rm ~/.docker/cli-plugins/docker-compose`."
6. Log B2a SHIPPED in agent task pipeline; notify Paco via `homelab_send_message` with report path.

**On Option A approval:** PD will request a spec amendment from Paco (mixing engines is enough risk to warrant the amendment to be in writing).

**On Option B approval:** PD will request a spec amendment from Paco that adjusts Steps 5-6 + gate 7 to v1 syntax.

**On reject all options:** PD stands down; CEO/Paco decide alternative target node or alternative strategy.

## Standing Rules / CLAUDE.md cross-check

- **Rule 1 (MCP fabric is for control, not bulk data):** task is local to Beast; preflight read-only via single-shell-command MCP calls. Compliant.
- **CLAUDE.md hard rule (Docker bypasses UFW):** spec already binds `127.0.0.1:5432:5432`. Compliant on whichever option lands.
- **CLAUDE.md hard rule (no synchronous self-restart of MCP):** N/A -- B2a does not touch homelab-mcp.service.
- **CLAUDE.md "Spec or no action":** honored by stopping here.

## Asks of Paco

1. Pick a remediation option (A / B / C / reject).
2. If Option C: confirm version pin (`v2.29.7` is current latest stable as of 2026-04-26 Day 72; PD will verify against `https://github.com/docker/compose/releases/latest` at install time and report the exact tag pulled).
3. If amendment needed (Option A or B): re-issue B2a with Step 0 added or Steps 5-6 rewritten.

PD waits for explicit ratification before resuming.

---

**File location:** `/home/jes/control-plane/docs/paco_request_b2a_compose_v2_blocker.md` (untracked, matching precedent of `docs/paco_request_r640_fan_control_idrac9_7x.md`)

-- PD
