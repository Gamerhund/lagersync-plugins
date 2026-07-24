#!/usr/bin/env python3
import json
import argparse
from pathlib import Path

def collect_results(baseline_file, latest_file, baseline_version, latest_version, output_file):
    baseline_results = []
    latest_results = []
    
    if Path(baseline_file).exists():
        with open(baseline_file) as f:
            baseline_results = json.load(f)
    
    if Path(latest_file).exists():
        with open(latest_file) as f:
            latest_results = json.load(f)
    
    baseline_pass = sum(1 for r in baseline_results if r.get("overall") == "PASS")
    latest_pass = sum(1 for r in latest_results if r.get("overall") == "PASS")
    
    combined = {
        "baseline": baseline_results,
        "latest": latest_results,
        "summary": {
            "total_plugins": len(set(r["plugin"] for r in baseline_results + latest_results)),
            "baseline_pass": baseline_pass,
            "latest_pass": latest_pass,
            "baseline_version": baseline_version,
            "latest_version": latest_version
        }
    }
    
    with open(output_file, "w") as f:
        json.dump(combined, f, indent=2)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline", required=True)
    parser.add_argument("--latest", required=True)
    parser.add_argument("--baseline-version", required=True)
    parser.add_argument("--latest-version", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    
    collect_results(args.baseline, args.latest, args.baseline_version, args.latest_version, args.output)

if __name__ == "__main__":
    main()
