#!/usr/bin/env python3
import json
import argparse
from pathlib import Path

def collect_results(baseline_file, latest_file, output_file):
    baseline_results = []
    latest_results = []
    
    if Path(baseline_file).exists():
        with open(baseline_file) as f:
            baseline_results = json.load(f)
    
    if Path(latest_file).exists():
        with open(latest_file) as f:
            latest_results = json.load(f)
    
    combined = {
        "baseline": baseline_results,
        "latest": latest_results,
        "summary": {
            "total_plugins": len(set(r["plugin"] for r in baseline_results + latest_results)),
            "baseline_pass": sum(1 for r in baseline_results if r["loading"] == "PASS" and r["initialization"] == "PASS"),
            "latest_pass": sum(1 for r in latest_results if r["loading"] == "PASS" and r["initialization"] == "PASS"),
            "baseline_version": "3.11",
            "latest_version": "3.12"
        }
    }
    
    with open(output_file, "w") as f:
        json.dump(combined, f, indent=2)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline", required=True)
    parser.add_argument("--latest", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    
    collect_results(args.baseline, args.latest, args.output)

if __name__ == "__main__":
    main()
