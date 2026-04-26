# P2 → Paco: R640 Fan Control Blocker — iDRAC9 7.00

2026-04-23 20:30 MDT. Spec paused at revised step 3b. No state change on TheBeast. Fan still at stock ~67% PWM / ~12k RPM.

## Situation
Sloan issued fan-reduction spec for TheBeast (R640, iDRAC 192.168.1.237). Original ipmitool raw path failed step 3 (`0x30 0xce 0x00 0x16 0x05 ...` → rsp=0xc1, Invalid Command). Your revised racadm spec picked up. Firmware check confirmed iDRAC9 **7.00.00.183**, build 03, last updated 2026-02-27 — past your 5.x/6.x threshold.

Ran revised step 3b (`racadm get system.thermalsettings`). New blocker identified.

## Firmware-7.00 deltas vs. your revised spec
- `MinimumFanSpeed=255` (auto sentinel) — nothing manually pinned today
- `ThermalProfile=Default Thermal Profile Settings` — stock
- `MFSMinimumLimit=15` — firmware floor; 30 / 25 / 20 targets all valid
- `#CurrentSystemProfileValue=Minimum Power` — BIOS system profile, separate domain
- `#PCIeSlotLFMSupport=Supported` — NEW in iDRAC9 4.40+. Per-slot Limit Fan Mode
- **`ThirdPartyPCIFanResponse` attribute absent** from `system.thermalsettings` output

Your step 3e `set system.thermalsettings.ThirdPartyPCIFanResponse 0` will fail "attribute not found" on this firmware.

## What likely happened
Dell reorganized thermal namespace in 7.x. `ThirdPartyPCIFanResponse` either:
(a) moved to a different group such as `system.thermalconfig.*` or `system.thermalhistoricalperfsettings.*` — [VERIFY]
(b) removed entirely, replaced by the newer `PCIeSlotLFMSupport` mechanism per-slot — [VERIFY]

Have not yet probed adjacent namespaces (read-only, safe, ~30s). Held for your call.

## Options

### A — Probe (read-only, recommended first move)
```
/tmp/idrac.exp 'racadm get system.thermalconfig'
/tmp/idrac.exp 'racadm help system.thermalsettings'
/tmp/idrac.exp 'racadm help system'
```
If the attribute is found in another group, proceed with original revised spec (substituting correct path).

### B — Proceed without it
`set ThermalProfile=1` + `set MinimumFanSpeed=30`. Skip `ThirdPartyPCIFanResponse`.
Risk: if Dell's PCIe third-party response was the actual force keeping fans at 67%, raising a floor but not disabling the force could mean the 30% floor is overridden by the ramp still coming from T4 detection. Possible outcome: no audible change after the "success" set. Fast to test, low hardware risk (iDRAC keeps auto safety).

### C — Use `PCIeSlotLFMSupport` (7.x-native path)
T4 is in Slot 2. Candidate attributes (unverified): `system.pcieslot.<n>.*` or `system.lfm.*`. Need to identify exact attribute name before writing anything. Forward-compatible for future firmware.

## P2 recommendation
A first (probe). Then:
- If `ThirdPartyPCIFanResponse` found elsewhere → original revised spec with corrected path
- If found only in LFM form → C
- If not available at all → B, with explicit acceptance that fan noise may not drop

## Side concerns
1. **T4 headroom tight.** Idle 69°C. Spec evaluation ceiling 75°C, abort 78°C. 6°C / 9°C from idle before load. Recommend 3–5 min stabilization per step (not 90s) and a synthetic T4 load during final evaluation (`gpu_burn` or equivalent) before declaring the setpoint survivable.

2. **SlimJim 192.168.1.40 offline** since the move today. MQTT broker down. Unrelated to fan work. Sloan to physically check.

3. **mcp-remote reconnect fragility.** Tailscale flapped during the move; mcp-remote on macmini hit its 2-retry max and died permanently. ~11-hour MCP outage, required manual kill + Claude Desktop restart. Follow-up spec candidates: (a) launchd supervisor with KeepAlive, (b) `--reconnect-max-attempts` flag if supported, (c) run homelab-mcp as local stdio on macmini instead of remote HTTP through Tailscale.

## Ask
Direction on A / B / C. Ready to move on receipt.

— P2
