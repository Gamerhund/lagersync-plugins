#!/usr/bin/env python3
import os
import json
import sys
from pathlib import Path

def generate_pr_comment(results_file):
    if not Path(results_file).exists():
        return "ℹ️ No runtime results available."
    
    with open(results_file) as f:
        data = json.load(f)
    
    baseline = data.get("baseline", [])
    latest = data.get("latest", [])
    summary = data.get("summary", {})
    
    comment = "🚀 Plugin Runtime Validation\n\n"
    
    if not baseline and not latest:
        comment += "ℹ️ No plugin changes detected. Runtime tests skipped.\n"
        return comment
    
    comment += f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    
    comment += f"🔍 Detection\n"
    comment += f"✅ {summary.get('total_plugins', 0)} plugin(s) tested\n\n"
    
    comment += f"🐍 Python Compatibility\n\n"
    
    comment += f"Python {summary.get('baseline_version', '3.11')} — Production Baseline\n"
    baseline_pass = summary.get('baseline_pass', 0)
    baseline_total = len(baseline)
    if baseline_pass == baseline_total:
        comment += f"✅ PASS ({baseline_pass}/{baseline_total})\n\n"
    else:
        comment += f"❌ FAIL ({baseline_pass}/{baseline_total})\n\n"
    
    comment += f"Python {summary.get('latest_version', '3.12')} — Latest\n"
    latest_pass = summary.get('latest_pass', 0)
    latest_total = len(latest)
    if latest_pass == latest_total:
        comment += f"✅ PASS ({latest_pass}/{latest_total})\n\n"
    else:
        comment += f"❌ FAIL ({latest_pass}/{latest_total})\n\n"
    
    comment += f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    
    if baseline:
        comment += f"⚙️ Runtime Results (Python {summary.get('baseline_version', '3.11')})\n\n"
        for result in baseline:
            plugin_name = result.get("plugin", "unknown")
            loading = result.get("loading", "UNKNOWN")
            initialization = result.get("initialization", "UNKNOWN")
            
            if loading == "PASS" and initialization == "PASS":
                comment += f"✅ {plugin_name}: PASS\n"
            else:
                comment += f"❌ {plugin_name}: FAIL\n"
                for error in result.get("errors", []):
                    comment += f"   Error: {error}\n"
        comment += "\n"
    
    if latest:
        comment += f"⚙️ Runtime Results (Python {summary.get('latest_version', '3.12')})\n\n"
        for result in latest:
            plugin_name = result.get("plugin", "unknown")
            loading = result.get("loading", "UNKNOWN")
            initialization = result.get("initialization", "UNKNOWN")
            
            if loading == "PASS" and initialization == "PASS":
                comment += f"✅ {plugin_name}: PASS\n"
            else:
                comment += f"❌ {plugin_name}: FAIL\n"
                for error in result.get("errors", []):
                    comment += f"   Error: {error}\n"
        comment += "\n"
    
    comment += f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    
    total_pass = baseline_pass + latest_pass
    total_tests = baseline_total + latest_total
    
    if total_pass == total_tests:
        comment += "🎯 RESULT: ✅ PASSED\n\n"
    else:
        comment += "🎯 RESULT: ❌ FAILED\n\n"
    
    return comment

def post_pr_comment(comment):
    import requests
    
    pr_number = os.environ.get("PR_NUMBER")
    repo = os.environ.get("GITHUB_REPOSITORY")
    token = os.environ.get("GITHUB_TOKEN")
    
    if not all([pr_number, repo, token]):
        print("Missing required environment variables")
        return
    
    url = f"https://api.github.com/repos/{repo}/issues/{pr_number}/comments"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    response = requests.post(url, json={"body": comment}, headers=headers)
    
    if response.status_code not in [200, 201]:
        print(f"Failed to post comment: {response.status_code}")
        print(response.text)
    else:
        print("PR comment posted successfully")

if __name__ == "__main__":
    results_file = "final-runtime-results.json"
    comment = generate_pr_comment(results_file)
    post_pr_comment(comment)
