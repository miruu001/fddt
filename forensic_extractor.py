# forensic_extractor.py
# the "investigator tool" - drives the TAP controller and target device to perform a JTAG-based forensic memory acquisition

import re


class ForensicExtractor:
   
    # simulates a forensic acquisition tool that uses JTAG (IEEE 1149.1) to halt a target device, dump its memory and search for artifacts

    ARTIFACT_PATTERNS = {
        "wifi_credential": rb"WIFI_PSK=[^\x00]+",
        "ssh_key_fragment": rb"ssh-rsa [A-Za-z0-9+/=]+",
        "process_info": rb"/usr/bin/[a-zA-Z0-9_]+ running pid=\d+",
    }

    def __init__(self, tap, device):
        self.tap = tap
        self.device = device
        self.dump = None
        self.artifacts_found = []
        self.log = []

    def _record(self, message):
        self.log.append(message)
        print(message)

    def acquire(self, dump_start=0, dump_length=None):
      
        # reset TAP
        self._record("[TAP] Resetting TAP controller...")
        self.tap.reset()
        self._record(f"[TAP] State: {self.tap.state}")

        # enter Shift-DR
        self._record("[TAP] Entering Shift-DR to access debug registers...")
        self.tap.goto_shift_dr()
        self._record(f"[TAP] State: {self.tap.state}")

        # halt target CPU
        self._record("[DEVICE] Sending halt request via JTAG...")
        try:
            status = self.device.halt()
        except PermissionError as e:
            self._record(f"[ERROR] {e}")
            return {"success": False, "reason": str(e)}

        self._record(f"[DEVICE] CPU halted. PC={status['pc']}")
        
        # read register state
        regs = {name: hex(self.device.read_register(name)) for name in self.device.registers}
        self._record(f"[DEVICE] Register snapshot: {regs}")

         # dump memory
        if dump_length is None:
            dump_length = self.device.memory_size - dump_start

        self._record(f"[DEVICE] Dumping memory [{dump_start}:{dump_start + dump_length}]...")
        self.dump = self.device.read_memory(dump_start, dump_length)
        self._record(f"[DEVICE] Dump complete: {len(self.dump)} bytes acquired.")

        # scan for artifacts
        self._scan_for_artifacts()

        self.device.resume()
        self._record("[DEVICE] CPU resumed. Acquisition complete.")

        return {
            "success": True,
            "registers": regs,
            "bytes_dumped": len(self.dump),
            "artifacts_found": self.artifacts_found,
        }

    def _scan_for_artifacts(self):
        # search the acquired dump for known forensic artifact
        
        self._record("[SCAN] Searching memory dump for artifacts...")
        for label, pattern in self.ARTIFACT_PATTERNS.items():
            matches = re.findall(pattern, self.dump)
            for match in matches:
                artifact = {
                    "type": label,
                    "value": match.decode("utf-8", errors="replace"),
                    "offset": self.dump.find(match),
                }
                self.artifacts_found.append(artifact)
                self._record(f"  [FOUND] {label}: {artifact['value']} (offset {artifact['offset']})")

        if not self.artifacts_found:
            self._record("  [SCAN] No artifacts found.")

    def save_dump(self, filename="memory_dump.bin"):
        if self.dump is None:
            raise RuntimeError("No dump available to save.")
        with open(filename, "wb") as f:
            f.write(self.dump)
        self._record(f"[SAVE] Dump written to {filename}")
        return filename
