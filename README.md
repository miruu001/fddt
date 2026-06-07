# Digital Forensics using IEEE 1149.1 (JTAG)
> **Course:** Fault Diagnosis and Design for Testability — Lab Paper  
> **Target Device:** Raspberry Pi 3 (Broadcom BCM2837)

---

## Overview

IEEE 1149.1, commonly known as **JTAG** (Joint Test Action Group), is a hardware interface standard originally designed for board-level testing of digital circuits. It provides direct access to a device's internal logic through a dedicated 4-wire serial interface (TDI, TDO, TCK, TMS).

In a **digital forensics** context, JTAG is valuable because it allows an investigator to:
- Halt a running CPU without touching the OS
- Read raw memory (RAM, flash) directly from hardware
- Bypass software-level security (locked bootloaders, encrypted storage keys in RAM)
- Extract a full memory image even from a powered-on, uncooperative device

This makes it a critical low-level acquisition technique when traditional software forensics tools fail.

---

## Hardware Setup

| Component | Details |
|---|---|
| Target device | Raspberry Pi 3 Model B (BCM2837 SoC, ARM Cortex-A53) |
| JTAG adapter | USB FT2232H-based adapter (e.g. Olimex ARM-USB-OCD-H) |
| Software | OpenOCD 0.12.0, GDB 13, binwalk, xxd |
| Host OS | Linux (Ubuntu 22.04) |

### JTAG Pin Connections (BCM2837)

| JTAG Signal | RPi 3 GPIO Pin | Physical Pin |
|---|---|---|
| TCK | GPIO 25 | Pin 22 |
| TMS | GPIO 27 | Pin 13 |
| TDI | GPIO 26 | Pin 37 |
| TDO | GPIO 24 | Pin 18 |
| GND | GND | Pin 6 |

> **Note:** JTAG is disabled by default on the Pi 3. It must be enabled by adding `enable_jtag_gpio=1` to `/boot/config.txt`.

---

## Forensic Acquisition Process

### 1. Connect and Initialize

Launch OpenOCD with the appropriate interface and target config:

```bash
openocd -f interface/ftdi/ft2232h.cfg -f target/bcm2835.cfg
```

Expected output:
Open On-Chip Debugger 0.12.0
Info : JTAG tap: bcm2835.cpu tap/device found: 0x07b7617f
Info : bcm2835.cpu: hardware has 6 breakpoints, 4 watchpoints


### 2. Halt the CPU

Connect via telnet and issue a halt:

```bash
telnet localhost 4444
```

halt
target halted in ARM state due to debug-request, current mode: Supervisor
pc: 0xc0a8f3bc cpsr: 0x600001d3


Halting freezes the CPU in place — memory contents are preserved exactly as they were at the moment of acquisition.

### 3. Dump RAM

Extract 64KB starting from the kernel base address:

```bash
dump_image ram_dump.bin 0xc0000000 0x10000
```

For a broader acquisition (full 1GB RAM — takes several minutes):

```bash
dump_image full_ram.bin 0x00000000 0x40000000
```

### 4. Inspect the Dump

Search for human-readable artifacts (passwords, tokens, keys):

```bash
strings ram_dump.bin | grep -i "password\|token\|key\|ssh"
```

Inspect raw hex for known file headers:

```bash
xxd ram_dump.bin | head -50
```

Use binwalk to detect embedded files or firmware structures:

```bash
binwalk ram_dump.bin
```

---

## What Can Be Recovered

Through JTAG-based memory acquisition on a Raspberry Pi 3, the following forensic artifacts are accessible:

- **Encryption keys** held in RAM (e.g. LUKS volume keys, SSH session keys)
- **Running process memory** — heap and stack contents of active processes
- **Network credentials** — Wi-Fi passphrases, auth tokens cached in memory
- **Firmware image** — full flash dump for offline analysis
- **CPU register state** — program counter, stack pointer at time of halt

---

## Limitations

- JTAG must be physically enabled on the Pi 3 (not available by default)
- Requires physical access to the device and its PCB header pins
- Full RAM dump is slow (~30–60 min for 1GB over JTAG)
- Some SoCs implement **JTAG fusing** (permanently disabled in production devices)
- Volatile memory (RAM) is lost if the device is powered off before acquisition

---

## Tools Used

| Tool | Purpose |
|---|---|
| OpenOCD | JTAG interface control, CPU halt, memory dump |
| GDB | Register inspection, live debugging |
| binwalk | Firmware/binary analysis |
| xxd | Hex dump inspection |
| strings | ASCII artifact extraction |

---

## References

1. IEEE Std 1149.1-2013 — *IEEE Standard for Test Access Port and Boundary-Scan Architecture*
2. OpenOCD User's Guide — https://openocd.org/doc/html/index.html
3. Cornelissen, J. et al. — *JTAG Explained: The Embedded Engineer's Companion*, 2019
