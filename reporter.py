# reporter.py
# saves forensic acquisition results into JSON

import json
import datetime


def save_report(result, scenario_name, filename_prefix="report"):
    
    # saves the result dict from ForensicExtractor.acquire() into JSON
    
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    report = {
        "scenario": scenario_name,
        "timestamp": timestamp,
        "result": result,
    }

    safe_name = scenario_name
    for char in [" ", "/", "\\", ":", "*", "?", '"', "<", ">", "|", "(", ")"]:
        safe_name = safe_name.replace(char, "_")

    ts_file = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    out_filename = f"{filename_prefix}_{safe_name}_{ts_file}.json"

    with open(out_filename, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(f"[REPORT] Saved to {out_filename}")
    return out_filename


def print_summary(result):

    # prints a readable summary of an acquisition result

    print("\n--- ACQUISITION SUMMARY ---")
    if not result.get("success"):
        print(f"FAILED: {result.get('reason')}")
        print("---------------------------\n")
        return

    print(f"Bytes dumped: {result['bytes_dumped']}")
    print(f"Registers: {result['registers']}")
    print(f"Artifacts found: {len(result['artifacts_found'])}")
    for artifact in result["artifacts_found"]:
        print(f"  - [{artifact['type']}] {artifact['value']} (offset {artifact['offset']})")
    print("---------------------------\n")
