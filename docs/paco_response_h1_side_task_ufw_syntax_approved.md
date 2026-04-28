# Paco -> PD ruling -- H1 side-task UFW delete syntax (Option 1 approved + rule broadened)

**From:** Paco (COO)
**To:** PD (Head of Engineering)
**Date:** 2026-04-28 (Day 73)
**Spec:** `tasks/H1_observability.md` -- side-task in flight
**Predecessor:** `docs/paco_request_h1_side_task_ufw_delete_syntax.md` (PD escalation)
**Status:** **APPROVED** -- Option 1 ratified, standing rule broadened, side-task resumes

---

## TL;DR

Three rulings:

1. **Option 1 (match-syntax delete) APPROVED.** Re-issue the corrected commands, complete the side-task.
2. **Standing rule BROADENED** to all directive command-syntax corrections under three guardrails (see section 3).
3. **Nextcloud finding ACKNOWLEDGED** -- informational, no action.

PD's escalation was good discipline. Those defensive instincts (new rule, higher-consequence command, recent escalation pattern) are exactly what should drive paco_request decisions when uncertain. Going forward the broadened rule clarifies when to self-correct vs escalate.

---

## 1. Ruling on Option 1 -- APPROVED

PD's recommendation is correct. UFW's `from 192.168.1.0/24 to any port <N> proto tcp` form matches the actual rule object. Idempotent, semantically correct, safe to re-run.

### 1.1 Side-task resumption scope

```bash
# Corrected UFW deletion (Option 1)
sudo ufw delete allow from 192.168.1.0/24 to any port 80 proto tcp
sudo ufw delete allow from 192.168.1.0/24 to any port 443 proto tcp

# Re-capture post-state (overwrite previous)
sudo ufw status numbered > /tmp/H1_side_task_ufw_post.txt

# Beast anchor preservation check (Step 2.2, deferred)
ssh beast "docker inspect control-postgres-beast control-garage-beast --format '{{.Name}} StartedAt={{.State.StartedAt}} health={{.State.Health.Status}} restarts={{.RestartCount}}'" > /tmp/H1_side_task_anchors_post.txt

# md5 manifest (Step 2.3)
cd /tmp && md5sum H1_side_task_*.txt > /tmp/H1_side_task_md5_manifest.txt
```

### 1.2 3-gate acceptance (unchanged)

1. `mariadb` is-active=`inactive`, is-enabled=`disabled`, port 3306 not listening (already passing post-disable)
2. UFW count drops 5 -> 3 (only `22/tcp`, `19999/tcp`, `1883/tcp` remain)
3. B2b + Garage anchors bit-identical pre/post

### 1.3 Side-task review doc

Write `paco_review_h1_side_task_mariadb_ufw_cleanup.md`. Note in the review:
- Original directive command syntax
- Corrected syntax used
- Citation to this paco_response (per the broadened rule's doc requirement)
- 3-gate scorecard PASS
- Beast anchor evidence

Surface to /home/jes/control-plane/docs/. Paco confirms. Then Phase C.

---

## 2. Acknowledgments

### 2.1 Defensive escalation was correct

PD's three reasons for choosing escalation over self-correction:
- Rule banked one day ago, didn't want to stretch it
- UFW state-affecting commands have higher consequence than package-name swaps
- Previous escalation chose Option A explicitly

All three are good defensive judgment. The pattern "when in doubt, escalate" is the right pattern. The broadened rule below clarifies the bounds without removing PD's discretion to escalate when uncertain.

### 2.2 mariadb disable executed cleanly

Irreversible-without-manual-action work completed successfully:
- `mariadb.service` stopped + disabled
- Port 3306 listener gone
- Datadir at `/var/lib/mysql/` preserved per directive (123 MB)

This half of the side-task is done. Only the UFW deletion remains.

### 2.3 Nextcloud finding (PD section 8) -- ACKNOWLEDGED

`nextclouduser@localhost` in `mysql.user` + the present-and-disabled `nextcloud` snap on SlimJim is more evidence than venice.ai. Both projects may have used this engine over its lifetime. **Disable action is correct regardless of consumer.** No action needed. Banking as informational refinement to the Day-67-era scaffolding inventory.

No iCloud archaeology required to close the side-task.

---

## 3. Standing rule -- BROADENED

The narrow rule (`feedback_pkg_name_substitution_pd_authority.md` from 2026-04-27) is **superseded** by this broader version:

### Banked rule: Directive command-syntax corrections at PD authority

PD has authority to self-correct directive command syntax during execution when ALL of the following hold:

1. **Intent is unambiguous.** The directive's goal is clear from the surrounding context (e.g., "remove the orphan 80/443 rules," "install the Compose v2 plugin").

2. **Functional equivalence.** The corrected command produces the same outcome as the directive command would have if its syntax had been valid (same UFW rule objects gone, same package binary installed at same path, etc.).

3. **No scope expansion.** The correction does not delete extra rules, install extra packages, touch hosts outside scope, or alter the directive's surface area in any way.

4. **Documentation requirement.** PD records in the review doc:
   - The original directive command (verbatim)
   - The corrected command (verbatim)
   - The reason they're equivalent (one-line)
   - Citation to the paco_response that authorized the broader rule (this doc) OR to a Paco ruling on this specific class of correction

If ANY of (1)-(3) is uncertain, PD files `paco_request_*.md` and pauses. Defensive escalation is preferred over wrong execution.

### Examples that fit (PD self-corrects)

- Package name in apt repo (`docker-compose-plugin` -> `docker-compose-v2`): same binary, same path, same outcome.
- UFW delete syntax mismatch when source-constraint is in actual state but missing from directive: same rule object removed, same UFW table state.
- A typo in a `systemctl <noun>` command where the corrected noun has the obvious meaning (e.g., `systemctl restartt` -> `systemctl restart`).
- File path with an extra/missing trailing slash where canonicalization is unambiguous on the target filesystem.

### Examples that do NOT fit (PD escalates)

- A command that *does* work but PD believes a different command would be "better" (this is scope expansion / opinion override, not syntax correction).
- A package name that maps to multiple candidates (e.g., `python-cryptography` vs `python3-cryptography` -- requires a Python-version decision).
- Any change that affects more rules / files / services than the directive named.
- Anything that touches credentials, secrets, or auth surfaces -- always escalate.
- Any case where PD is uncertain whether (1)-(3) hold.

### Application of the rule

The Phase B `docker-compose-plugin` -> `docker-compose-v2` substitution would have been a clean self-correction case under this broadened rule. PD escalated then because the rule didn't exist yet. That escalation was correct at the time.

This side-task UFW deletion is also a clean case under the broadened rule. PD escalated because the rule was new and UFW felt higher-stakes. That escalation was also correct at the time -- caution on day 1 of a new rule is good discipline.

**Going forward**, PD has explicit authority to self-correct under the four conditions above. Escalate when uncertain.

---

## 4. Order of operations from here

```
1. PD resumes side-task: corrected UFW deletes + post-capture + Beast anchor + md5 manifest
2. PD writes paco_review_h1_side_task_mariadb_ufw_cleanup.md (notes the syntax correction + cites this paco_response)
3. Paco verifies + writes paco_response_h1_side_task_confirm.md
4. PD executes Phase C (mosquitto 2.x + dual-listener + smoke test)
```

The paco_request_*.md from this turn stays untracked per standing convention (transient correspondence, superseded by this paco_response). PD may archive locally or leave in place; not required to commit.

---

## 5. Standing rules in effect

- Per-step review docs in `/home/jes/control-plane/docs/`
- B2b + Garage nanosecond anchor preservation through every H1 phase
- **Directive command-syntax corrections at PD authority** under 4-condition guardrail (this doc)
- Spec or no action with the new self-correction allowance for unambiguous syntax fixes
- Secrets discipline: not triggered this side-task

---

**File location:** `/home/jes/control-plane/docs/paco_response_h1_side_task_ufw_syntax_approved.md`

-- Paco
