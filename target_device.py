# target_device.py
# simulates a target SoC with registers and memory accessible via JTAG

import random

class Register:
    def __init__(self, name, value=0):
        self.name = name
        self.value = value


class TargetDevice:
    
    # simulates the internal state of a target device reachable via JTAG: CPU registers, RAM contents, lock flag

    def __init__(self, memory_size=4096, locked=False):
        self.memory_size = memory_size
        self.memory = bytearray(random.getrandbits(8) for _ in range(memory_size))
        self.registers = {
            "PC": Register("PC", 0xC0008000),
            "SP": Register("SP", 0xC03FFFF0),
            "R0": Register("R0", 0x00000000),
            "R1": Register("R1", 0x00000001),
        }
        self.halted = False
        self.locked = locked  # True = JTAG access fused/disabled (secure device)
        self._plant_artifacts()

    # plants realistic 'forensic' artifacts inside memory to simulate what an investigator could recover from a real device: wifi password, SSH key fragment and a process name string
    def _plant_artifacts(self):
        artifacts = [
            b"WIFI_PSK=Summer2026!",
            b"ssh-rsa AAAAB3NzaC1yc2EAAAADAQABfakekeyfragment",
            b"/usr/bin/sshd running pid=812",
        ]
        for artifact in artifacts:
            start = random.randint(0, self.memory_size - len(artifact) - 1)
            self.memory[start:start + len(artifact)] = artifact

    def halt(self):
        # simulates halting the CPU via JTAG debug request
        if self.locked:
            raise PermissionError("JTAG access denied: device is fused/locked.")
        self.halted = True
        return {"pc": hex(self.registers["PC"].value), "status": "halted"}

    def read_register(self, name):
        if not self.halted:
            raise RuntimeError("Cannot read registers: CPU is not halted.")
        return self.registers[name].value

    def read_memory(self, start, length):
        if not self.halted:
            raise RuntimeError("Cannot dump memory: CPU is not halted.")
        if start < 0 or start + length > self.memory_size:
            raise ValueError("Requested memory range out of bounds.")
        return bytes(self.memory[start:start + length])

    def resume(self):
        self.halted = False
