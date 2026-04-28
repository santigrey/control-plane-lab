# Paco -> PD response -- H1 Phase B package-name correction (proceed)

**From:** Paco (COO)
**To:** PD (Head of Engineering)
**Date:** 2026-04-28 (Day 73)
**Spec:** `tasks/H1_observability.md` section 6
**Predecessor:** PD blocked-status report 2026-04-28 (package `docker-compose-plugin` not in Ubuntu 24.04 repos)
**Status:** **AUTHORIZED** -- proceed with corrected package name `docker-compose-v2`

---

## Ruling

**Install `docker-compose-v2` (Ubuntu 24.04 universe repo, candidate 2.40.3+ds1-0ubuntu1~24.04.1) instead of `docker-compose-plugin`.** Single-line apt swap. Functionally identical -- both install `/usr/libexec/docker/cli-plugins/docker-compose` exposing the `docker compose` v2 CLI.

## Why this happened

My directive used the package name from Docker CE's apt repo (`docker-compose-plugin`). Ubuntu 24.04 ships docker.io from the universe repo, with the matching plugin named `docker-compose-v2`. They are the same plugin, just packaged differently:

| Source | Docker package | Compose plugin package |
|---|---|---|
| Docker CE repo (download.docker.com) | `docker-ce` | `docker-compose-plugin` |
| Ubuntu universe (default 24.04 install) | `docker.io` | **`docker-compose-v2`** |

SlimJim has `docker.io 28.2.2-0ubuntu1~24.04.1` -> we're on the universe path -> the correct plugin name is `docker-compose-v2`.

## Process correction (banking)

This kind of package-name correction within the agreed strategy is at PD's authority -- not an escalation event. Going forward: if PD encounters a package name that doesn't exist but a clearly-equivalent one does, swap it and document in the review doc. Don't block.

Banking as a future-spec rule: **"Package names in Paco specs are advisory; PD verifies and corrects to the matching package on the target distro before install. Document substitution in the review doc."**

## Phase B directive (corrected)

Proceed per `tasks/H1_observability.md` section 6 with this single substitution:

```bash
# Spec text:    sudo apt install -y docker-compose-plugin
# CORRECTED:    sudo apt install -y docker-compose-v2
```

All other Phase B steps (pre-flight, install, group, refresh shell, verify, anchor preservation check, 4-gate acceptance) unchanged.

PD's review doc must include:
1. Package name substitution noted (this paco_response cited)
2. `apt-cache policy docker-compose-v2` output before install (showing universe repo source)
3. Standard 4-gate acceptance scorecard
4. B2b + Garage anchor evidence

---

**File location:** `/home/jes/control-plane/docs/paco_response_h1_phase_b_pkg_name_correction.md`

-- Paco
