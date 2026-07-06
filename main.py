# main.py
# runs the JTAG-based digital forensics acquisition demo across multiple scenarios: normal device, locked/fused device and a tampered device with different artifacts.

from tap_controller import TAPController
from target_device import TargetDevice
from forensic_extractor import ForensicExtractor
from reporter import save_report, print_summary


def run_scenario(name, locked=False, memory_size=4096):
    print(f"\n{'#'*60}")
    print(f" SCENARIO: {name}")
    print(f"{'#'*60}")

    tap = TAPController()
    device = TargetDevice(memory_size=memory_size, locked=locked)
    extractor = ForensicExtractor(tap, device)

    result = extractor.acquire()
    print_summary(result)

    if result.get("success"):
        extractor.save_dump(filename=f"dump_{name.replace(' ', '_')}.bin")

    save_report(result, scenario_name=name)
    return result


def main():
    print("\n" + "=" * 60)
    print(" JTAG DIGITAL FORENSICS TOOL — IEEE 1149.1 Simulation")
    print(" Simulated target: Raspberry Pi 3 (BCM2837)")
    print("=" * 60)

    results = []

    # scenario 1: Normal, unlocked device - full acquisition
    results.append(("1. Unlocked device - full acquisition",
                     run_scenario("Unlocked_Device_Acquisition", locked=False)))

    # scenario 2: Locked/fused device - JTAG access denied
    results.append(("2. Locked device - access denied",
                     run_scenario("Locked_Device_Access_Denied", locked=True)))

    # scenario 3: Larger memory dump - more artifacts likely found
    results.append(("3. Large memory acquisition",
                     run_scenario("Large_Memory_Acquisition", locked=False, memory_size=16384)))

    print("\n" + "=" * 60)
    print(" FINAL SUMMARY")
    print("=" * 60)
    for name, result in results:
        status = "SUCCESS" if result.get("success") else "BLOCKED"
        print(f" {name:<45} {status}")
    print("=" * 60)
    print("\nJSON reports and .bin dumps saved in current directory.\n")


if __name__ == "__main__":
    main()
