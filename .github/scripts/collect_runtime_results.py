#!/usr/bin/env python3
import json
import argparse
from pathlib import Path


def _safe_json_path(p):
    """Nur .json-Dateien im Arbeitsordner zulassen (CI-Argumente, Sonar S8707)."""
    base = Path.cwd().resolve()
    path = (base / str(p)).resolve()
    if path.suffix != ".json" or (path != base and base not in path.parents):
        raise SystemExit(f"Ungültiger Pfad: {p}")
    return path

def collect_results(baseline_file, latest_file, baseline_version, latest_version, output_file):
    baseline_results = []
    latest_results = []
    
    baseline_file = _safe_json_path(baseline_file)
    latest_file = _safe_json_path(latest_file)
    output_file = _safe_json_path(output_file)

    if baseline_file.exists():
        with open(baseline_file, encoding="utf-8") as f:
            baseline_results = json.load(f)
    
    if latest_file.exists():
        with open(latest_file, encoding="utf-8") as f:
            latest_results = json.load(f)
    
    baseline_pass = sum(1 for r in baseline_results if r.get("overall") == "PASS")
    latest_pass = sum(1 for r in latest_results if r.get("overall") == "PASS")
    
    combined = {
        "baseline": baseline_results,
        "latest": latest_results,
        "summary": {
            "total_plugins": len({r["plugin"] for r in baseline_results + latest_results}),
            "baseline_pass": baseline_pass,
            "latest_pass": latest_pass,
            "baseline_version": baseline_version,
            "latest_version": latest_version
        }
    }
    
    with open(output_file, "w", encoding="utf-8") as f:
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
