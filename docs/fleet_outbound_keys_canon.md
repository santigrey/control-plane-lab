# fleet_outbound_keys_canon

**Maintained by:** Paco | **Status:** ACTIVE | **Last updated:** 2026-05-02 Day 78 mid-day (Step 4.2 close)
**Tracks:** `docs/homelab_reachability_v1_0.md` reachability cycle Step 4.1 (outbound key generation on Goliath, KaliPi, Pi3) and Step 4.3 (canonical authorized_keys aggregation).

---

## Purpose

Authoritative inventory of every device's **outbound** SSH public key (the key the device uses to authenticate TO other devices). This is the source-of-truth for Step 4.3 canonical `authorized_keys` construction: the canonical authorized_keys on every Class A Linux node is the union of these keys (filtered by access policy).

Does NOT govern host keys (the keys remote devices use to identify themselves to clients via known_hosts) — those are managed by sshd at install time and are out of scope for this canon.

## Naming convention

All Paco-managed keys use comment `jes@<canonical-node-name>-canonical` where canonical-node-name is the LAN hostname per `homelab_reachability_v1_0.md` Step 3 canonical hosts block (ciscokid, beast, slimjim, goliath, kalipi, pi3, macmini, jesair).

CEO-supplied keys (Cortez, JesAir) may retain their organic comments; the comment is metadata, the key material is what matters for trust.

## Inventory (Class A Linux nodes; all keys verified live 2026-05-02 Day 78 mid-day)

| Node | Comment | Public key |
|---|---|---|
| CK | `jes@sloan3` (legacy; canonicalize at Step 6) | `ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIKk48m0m/IUkVfy/8ErpRsCIfrp5qivanpuXCTDCudwL` |
| Beast | `jes@beast-atlas-agent-day78` (Day 78 morning; canonicalize at Step 6) | `ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIGmptnRq3B0IO15psjFsjxHdFdnIWASfnk2tvPwoBzgt` |
| SlimJim | `slimjim-job-pipeline` (Day 30 historical; canonicalize at Step 6) | `ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIDWxK4q3Gt5doIeGGBCGBd4LBmkQPP1/P3lSGUig7RYN` |
| Goliath | `jes@goliath-canonical` (Day 78 mid-day Step 4.1) | `ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIMPekWj6KYOevrsnBZMPur6jXexQ+INkiE5hdPu1AlJc` |
| KaliPi | `jes@kalipi-canonical` (Day 78 mid-day Step 4.1) | `ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIG06kww+LqP2kf/nnIxXESsbWI68HgMRZKo5EhrzO1qk` |
| Pi3 | `jes@pi3-canonical` (Day 78 mid-day Step 4.1) | `ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIKTvEdw2FtSVTS31Z0dEvA4zA9kJ3B7+MyzoYCJ/yLEG` |
| Mac mini | TBD (Step 5; sshd unreachable; key may pre-exist or need generation) | TBD |

## CEO-supplied (Step 4.2)

| Device | Comment (organic) | Public key | Status |
|---|---|---|---|
| Cortez (Windows; user `sloan` per Y1 carve-out) | `sloan@cortez-canonical` (file-on-disk says `sloan@Cortez`; comment-canonicalized at Step 4.3 in authorized_keys block) | `ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAINUzV2aS51hKWDNIFkFoZ3KWyxMskcIw0OBGNB2NaXiq` | collected Day 78 mid-day |
| JesAir (macOS; user `jes`) | `jes@jesair-canonical` (file-on-disk says `jesair->macmini`; comment-canonicalized at Step 4.3 in authorized_keys block) | `ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAILgFiPCnSH6mEBYd9FeR4xcsoeZV1JMI1AKYWfq2ZPcK` | collected Day 78 mid-day |

## Fingerprints (SHA256, for at-a-glance verification)

- Goliath: `SHA256:v9d2E2fR7AHFbfKwE61C0y4JGDrYFaDvvvsgr+NsZSY`
- KaliPi: `SHA256:TjP4XSsohcqXf6MZjr2vHOI5+lyhyNhj4MkXjqQntss`
- Pi3: `SHA256:Xil+H0/6Dqui0E+XNUgrMuqAXpT5SrcddxldoOwCnuk`
- Cortez: backfill at Step 6
- JesAir: backfill at Step 6
- (CK/Beast/SlimJim: backfill at Step 6)

## Canonical authorized_keys construction (preview — Step 4.3)

Class A Linux nodes (CK, Beast, SlimJim, Goliath, KaliPi, Pi3, Mac mini) receive an authorized_keys file containing the union of:

1. All Class A Linux node outbound keys (so any node can SSH to any other as `jes`)
2. Cortez outbound key (Windows; `sloan@cortez` per Y1; access required for CEO administration)
3. JesAir outbound key (macOS; `jes@jesair` for CEO administration)

Total: 9 keys per Class A node post-Step-4.3 (8 once Cortez/JesAir resolve to one shared CEO admin key set, depending on CEO configuration).

Canonical authorized_keys file is reproducible: deterministic order (alphabetical by canonical name), one key per line, marker block delimited (parallel to `/etc/hosts` Step 3 pattern):

```
# BEGIN santigrey canonical authorized_keys (managed; see fleet_outbound_keys_canon.md)
<beast key>
<ciscokid key>
<cortez key>
<goliath key>
<jesair key>
<kalipi key>
<macmini key>
<pi3 key>
<slimjim key>
# END santigrey canonical authorized_keys
```

Idempotent install pattern (parallel to Step 3 Python heredoc): replace marker block in-place if present, append if absent. Pre-existing non-canonical keys logged to Step 6 audit but left untouched at Step 4.3 (they're additional grants, not within canonical scope).

## Stale-key audit log (Step 6 cleanup queue)

Keys discovered in existing authorized_keys files Day 78 mid-day verification, NOT in canonical inventory above:

- `macmini->github` (Beast, SlimJim, Goliath) — Mac mini key for GitHub deploy access; verify at Step 5 if still active; remove if unused
- ~~`jesair->macmini`~~ (Beast, SlimJim) — RESOLVED Day 78 mid-day Step 4.2: this IS JesAir canonical outbound key; only the comment differs from `jes@jesair-canonical`. Step 4.3 push will use canonical comment; pre-existing entries left untouched at 4.3 (Step 6 may consolidate).
- ~~`sloan@Cortez`~~ (Beast, SlimJim, Goliath) — RESOLVED Day 78 mid-day Step 4.2: this IS Cortez canonical outbound key; Cortez file-on-disk uses capital-C `Cortez`; canon comment will be `sloan@cortez-canonical`. Step 4.3 push will use canonical comment.
- `sloan@cortez` (Beast only, lowercase) — verify at Step 6: same key material as `sloan@Cortez`? If so, dedupe; if different, investigate provenance.
- `macmini-aioperator` (Goliath only) — Mac mini AI Operator runtime key; verify at Step 5

Resolution at Step 6: confirm each is either (a) replaced by a canonical entry collected via Step 4.2/Step 5, OR (b) explicitly purposed (additional grant) and kept with a comment update.
