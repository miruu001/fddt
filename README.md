**Curs: Fault Diagnosis and Design for Testability — Lab Paper**
**Topic: Digital Forensics using IEEE 1149.1 (JTAG)**

---

## What this project does

This project implements a **software simulation of a JTAG-based digital
forensics acquisition tool**. It models the IEEE 1149.1 TAP (Test Access
Port) controller, a simulated target device (based on a Raspberry Pi 3 /
BCM2837-class SoC), and a forensic extraction tool that uses the TAP state
machine to halt the CPU, read its registers, dump its memory and scan the
dump for recoverable artifacts (credentials, keys, process info).

No physical hardware is required to demonstrate the acquisition workflow:
every step (TAP state transitions, halt request, register read, memory
dump, artifact scan) follows the exact protocol logic used by real JTAG
debug probes and forensic tools such as OpenOCD, just modeled in Python.

---

## Why JTAG matters for digital forensics

IEEE 1149.1 (JTAG) was designed for board-level testing, but it also gives
an investigator low-level, OS-independent access to a device's internal
state. Because JTAG operates below the operating system, it can:

- Halt the CPU without the OS being aware
- Read raw memory directly from silicon, including data an attacker or
  suspect never intended to expose (cached passwords, session keys,
  process artifacts)
- Bypass user-level security in cases where physical access is available
  but software-level extraction is blocked

This makes it a critical acquisition technique when standard forensic
software tools cannot reach the data.

---

## Project structure

```
jtag_forensics_tool/
├── main.py                — runs all acquisition scenarios
├── tap_controller.py      — IEEE 1149.1 TAP state machine (16 states)
├── target_device.py       — simulated target: registers, memory, secrets
├── forensic_extractor.py  — the "tool": halt, dump, scan for artifacts
├── reporter.py            — saves JSON acquisition reports
└── README.md              — this file
```

---

## How the TAP controller works

The `TAPController` class implements the 16-state finite state machine
defined by IEEE 1149.1. The controller is always in exactly one state, and
moves to a new state only when a clock pulse (TCK) is applied while
holding a specific TMS (Test Mode Select) bit - 0 or 1. The `transitions`
dictionary encodes the official state diagram: for each state, it defines
where TMS=0 and TMS=1 lead.

Two convenience methods drive common sequences:

- `goto_shift_dr()` - sends TMS bits `1, 0, 0` from Run-Test/Idle, landing
  in **Shift-DR**, the state used to shift actual data (memory/register
  values) in or out
- `goto_shift_ir()` - sends TMS bits `1, 1, 0, 0` from Run-Test/Idle,
  landing in **Shift-IR**, the state used to load an instruction (e.g.
  "read memory") before data is transferred

In a full real-world acquisition, the tool typically enters Shift-IR first
to select the debug instruction, then Shift-DR to move the actual data.
This simulation goes directly to Shift-DR for simplicity, since the
instruction-selection step does not change the outcome being demonstrated.

`reset()` reproduces the standard JTAG reset trick: holding TMS=1 for five
clock cycles guarantees a return to Test-Logic-Reset regardless of the
starting state, since every state's TMS=1 path eventually leads there.

---

## The simulated target device

`TargetDevice` models a Raspberry Pi 3–class SoC (BCM2837) with:

- A register file (PC, SP, R0, R1)
- A memory array pre-loaded with random bytes plus three planted
  forensic artifacts: a Wi-Fi credential, an SSH key fragment and a
  running-process string
- An optional `locked` flag, simulating a device with JTAG fused/disabled
  (a common hardening measure on production/secure chips)

---

## Test scenarios

| # | Scenario | Expected result |
|---|----------|-----------------|
| 1 | Unlocked device - full acquisition | SUCCESS, all 3 artifacts found |
| 2 | Locked device - JTAG access denied | BLOCKED, `PermissionError` raised |
| 3 | Large memory acquisition (16 KB) | SUCCESS, artifacts found at different offsets |

---

## How to run

### Requirements
- Python 3.x (no external libraries needed)

### Steps
1. Put all `.py` files in a folder, e.g. `jtag_forensics_tool`
2. Open a terminal in that folder
3. Run:
```bash
python3 main.py
```

---

## Example output

```
############################################################
 SCENARIO: Unlocked_Device_Acquisition
############################################################
[TAP] Resetting TAP controller...
[TAP] State: Run-Test/Idle
[TAP] Entering Shift-DR to access debug registers...
[TAP] State: Shift-DR
[DEVICE] Sending halt request via JTAG...
[DEVICE] CPU halted. PC=0xc0008000
[DEVICE] Register snapshot: {'PC': '0xc0008000', 'SP': '0xc03ffff0', 'R0': '0x0', 'R1': '0x1'}
[DEVICE] Dumping memory [0:4096]...
[DEVICE] Dump complete: 4096 bytes acquired.
[SCAN] Searching memory dump for artifacts...
  [FOUND] wifi_credential: WIFI_PSK=Summer2026! (offset 512)
  [FOUND] ssh_key_fragment: ssh-rsa AAAAB3NzaC1yc2EAAAADAQABfakekeyfragment (offset 1801)
  [FOUND] process_info: /usr/bin/sshd running pid=812 (offset 3255)
[DEVICE] CPU resumed. Acquisition complete.

############################################################
 SCENARIO: Locked_Device_Access_Denied
############################################################
[TAP] Resetting TAP controller...
[DEVICE] Sending halt request via JTAG...
[ERROR] JTAG access denied: device is fused/locked.

============================================================
 FINAL SUMMARY
============================================================
 1. Unlocked device - full acquisition         SUCCESS
 2. Locked device - access denied              BLOCKED
 3. Large memory acquisition                   SUCCESS
============================================================
```

---

## JSON reports

Each scenario produces a timestamped JSON report, e.g.
`report_Unlocked_Device_Acquisition_20260706_100733.json`:

```json
{
  "scenario": "Unlocked_Device_Acquisition",
  "timestamp": "2026-07-06 10:07:33",
  "result": {
    "success": true,
    "registers": {"PC": "0xc0008000", "SP": "0xc03ffff0", "R0": "0x0", "R1": "0x1"},
    "bytes_dumped": 4096,
    "artifacts_found": [
      {"type": "wifi_credential", "value": "WIFI_PSK=Summer2026!", "offset": 512},
      {"type": "ssh_key_fragment", "value": "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABfakekeyfragment", "offset": 1801},
      {"type": "process_info", "value": "/usr/bin/sshd running pid=812", "offset": 3255}
    ]
  }
}
```

A raw binary dump (`dump_<scenario>.bin`) is also saved for each successful
acquisition, mirroring the `.bin` output a real JTAG probe would produce.

---

## Limitations

- The simulation models the JTAG protocol and forensic workflow correctly,
  but does not drive real electrical signals or a physical chip
- Real acquisitions must physically enable JTAG on the target (disabled by
  default on the Raspberry Pi 3) and require a JTAG adapter (e.g. FT2232H)
- Full RAM dumps over real JTAG hardware are much slower (minutes, not
  milliseconds) due to the serial nature of the interface
- Production/secure devices often permanently fuse off JTAG, which this
  project represents through the `locked` flag

---

## References

1. IEEE Std 1149.1-2013 — *IEEE Standard for Test Access Port and
   Boundary-Scan Architecture*
2. OpenOCD User's Guide — https://openocd.org/doc/html/index.html
3. Cornelissen, J. et al. — *JTAG Explained: The Embedded Engineer's
   Companion*, 2019
