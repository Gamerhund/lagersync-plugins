#!/usr/bin/env python3
import os
import json
import sys
from pathlib import Path

COMMENT_MARKER = "<!-- plugin-runtime-validation -->"


def _format_details(details, indent="   ", _depth=0):
    if not isinstance(details, dict) or not details:
        return ""
    lines = []
    for key, value in details.items():
        if key == "actual" and isinstance(value, (dict, list)):
            lines.append(f"{indent}{key}: {json.dumps(value, ensure_ascii=False)[:200]}")
        elif isinstance(value, dict):
            lines.append(f"{indent}{key}:")
            lines.append(_format_details(value, indent=indent + "   ", _depth=_depth + 1).rstrip("\n"))
        elif isinstance(value, list):
            lines.append(f"{indent}{key}: {', '.join(str(v) for v in value)}")
        else:
            lines.append(f"{indent}{key}: {value}")
    return "\n".join(lines) + "\n"

def generate_pr_comment(results_file):
    if not Path(results_file).exists():
        return "ℹ️ No runtime results available."
    
    with open(results_file) as f:
        data = json.load(f)
    
    baseline = data.get("baseline", [])
    latest = data.get("latest", [])
    summary = data.get("summary", {})
    
    comment = f"{COMMENT_MARKER}\n\n"
    comment += "🚀 Plugin Runtime & Compatibility Validation\n\n"
    
    if not baseline and not latest:
        comment += "ℹ️ No plugin changes detected. Runtime validation skipped.\n"
        return comment
    
    comment += f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    
    # Show results for each plugin
    all_results = baseline + latest
    for result in all_results:
        plugin_name = result.get("plugin", "unknown")
        python_version = result.get("python_version", "unknown")
        
        comment += f"Plugin: `{plugin_name}`\n"
        comment += f"Python: {python_version}\n\n"
        
        comment += f"🔍 Detection\n"
        detection = result.get("detection", "UNKNOWN")
        if detection == "PASS":
            comment += f"✅ Plugin automatically detected\n\n"
        else:
            comment += f"❌ {detection}\n"
            for error in result.get("errors", []):
                comment += f"   Error: {error}\n"
            comment += "\n"
        
        comment += f"📋 Metadata\n"
        metadata = result.get("metadata", "UNKNOWN")
        if metadata == "PASS":
            comment += f"✅ plugin.json valid\n\n"
        elif metadata == "NOT_APPLICABLE":
            comment += f"⏭️ NOT_APPLICABLE\n\n"
        else:
            comment += f"❌ {metadata}\n"
            for error in result.get("errors", []):
                if "metadata" in error.lower():
                    comment += f"   Error: {error}\n"
            comment += "\n"
        
        comment += f"⚙️ Runtime\n"
        loading = result.get("loading", "UNKNOWN")
        registration = result.get("registration", "UNKNOWN")
        
        if loading == "PASS":
            comment += f"✅ Backend loaded\n"
        elif loading == "NOT_APPLICABLE":
            comment += f"⏭️ No backend.py\n"
        else:
            comment += f"❌ {loading}\n"
        
        if registration == "PASS":
            comment += f"✅ Plugin registered\n"
        elif registration == "NOT_APPLICABLE":
            comment += f"⏭️ No blueprint\n"
        else:
            comment += f"❌ {registration}\n"
        comment += "\n"
        
        comment += f"💾 Database Initialization\n"
        db_init = result.get("database_initialization", "UNKNOWN")
        if db_init == "PASS":
            comment += f"✅ Tables created\n"
            db_details = result.get("details", {}).get("database_initialization", {})
            created = db_details.get("created_tables", [])
            if created:
                comment += f"   Created: {', '.join(created)}\n"
        elif db_init == "NOT_APPLICABLE":
            comment += f"⏭️ NOT_APPLICABLE\n"
        else:
            comment += f"⏭️ {db_init}\n"
        comment += "\n"
        
        comment += f"🔗 Route Discovery\n"
        route_disc = result.get("route_discovery", "UNKNOWN")
        if route_disc == "PASS":
            comment += f"✅ Routes discovered\n"
            route_details = result.get("details", {}).get("route_discovery", {})
            routes = route_details.get("routes", [])
            if routes:
                comment += f"   Found: {len(routes)} route(s)\n"
                for route in routes[:5]:
                    comment += f"   - {route}\n"
        elif route_disc == "NOT_APPLICABLE":
            comment += f"⏭️ NOT_APPLICABLE\n"
        else:
            comment += f"⏭️ {route_disc}\n"
        comment += "\n"
        
        comment += f"🔧 Function Discovery\n"
        func_disc = result.get("function_discovery", "UNKNOWN")
        if func_disc == "PASS":
            comment += f"✅ Functions discovered\n"
            func_details = result.get("details", {}).get("function_discovery", {})
            func_count = func_details.get("count", 0)
            comment += f"   Found: {func_count} callable function(s)\n"
        elif func_disc == "NOT_APPLICABLE":
            comment += f"⏭️ NOT_APPLICABLE\n"
        else:
            comment += f"⏭️ {func_disc}\n"
        comment += "\n"
        
        comment += f"🧪 Real Smoke Test\n"
        smoke_test = result.get("smoke_test", "UNKNOWN")
        if smoke_test == "PASS":
            comment += f"✅ Real functionality executed\n"
            smoke_details = result.get("details", {}).get("smoke_test", {})
            comment += _format_details(smoke_details, indent="   ")
        elif smoke_test == "SKIP":
            comment += f"⏭️ SKIP\n"
            reason = result.get("skip_reasons", {}).get("smoke_test", "")
            if reason:
                comment += f"   ({reason})\n"
        elif smoke_test == "NOT_APPLICABLE":
            comment += f"⏭️ NOT_APPLICABLE\n"
        else:
            comment += f"❌ {smoke_test}\n"
            for error in result.get("errors", []):
                if "smoke" in error.lower():
                    comment += f"   Error: {error}\n"
        comment += "\n"
        
        comment += f"🌐 API Test\n"
        api_test = result.get("api_test", "UNKNOWN")
        if api_test == "PASS":
            comment += f"✅ Blueprint registered\n"
            api_details = result.get("details", {}).get("api_test", {})
            if api_details:
                note = api_details.get("note", "")
                if note:
                    comment += f"   Note: {note}\n"
        elif api_test == "SKIP":
            comment += f"⏭️ SKIP\n"
            reason = result.get("skip_reasons", {}).get("api_test", "")
            if reason:
                comment += f"   ({reason})\n"
        elif api_test == "NOT_APPLICABLE":
            comment += f"⏭️ NOT_APPLICABLE\n"
        else:
            comment += f"❌ {api_test}\n"
        comment += "\n"
        
        comment += f"🔌 External Services\n"
        ext_services = result.get("external_services", "UNKNOWN")
        if ext_services == "PASS":
            comment += f"✅ External services mocked\n"
            ext_details = result.get("details", {}).get("external_services", {})
            mocked = ext_details.get("mocked", [])
            if mocked:
                comment += f"   Mocked: {', '.join(mocked)}\n"
        elif ext_services == "SKIP":
            comment += f"⏭️ SKIP\n"
        else:
            comment += f"⏭️ {ext_services}\n"
        comment += "\n"
        
        comment += f"⚡ Side Effects\n"
        side_effects = result.get("side_effects", "UNKNOWN")
        if side_effects == "PASS":
            comment += f"✅ Side effects validated\n"
            side_details = result.get("details", {}).get("side_effects", {})
            if side_details:
                db_changes = side_details.get("db_changes", [])
                if db_changes:
                    comment += f"   DB changes: {len(db_changes)}\n"
                note = side_details.get("note", "")
                if note:
                    comment += f"   Note: {note}\n"
        elif side_effects == "NOT_APPLICABLE":
            comment += f"⏭️ NOT_APPLICABLE\n"
        else:
            comment += f"⏭️ {side_effects}\n"
        comment += "\n"
        
        comment += f"🔐 Authentication\n"
        auth_test = result.get("authentication_test", "UNKNOWN")
        if auth_test == "PASS":
            comment += f"✅ Authentication tested\n"
        elif auth_test == "SKIP":
            comment += f"⏭️ SKIP\n"
            reason = result.get("skip_reasons", {}).get("authentication_test", "")
            if reason:
                comment += f"   ({reason})\n"
        elif auth_test == "NOT_APPLICABLE":
            comment += f"⏭️ NOT_APPLICABLE\n"
        else:
            comment += f"⏭️ {auth_test}\n"
        comment += "\n"
        
        comment += f"🛡️ Error Handling\n"
        error_handling = result.get("error_handling", "UNKNOWN")
        if error_handling == "PASS":
            comment += f"✅ Error handling validated\n"
            error_details = result.get("details", {}).get("error_handling", {})
            if error_details:
                tested = error_details.get("tested", "")
                if tested:
                    comment += f"   Tested: {tested}\n"
        elif error_handling == "SKIP":
            comment += f"⏭️ SKIP\n"
        else:
            comment += f"⏭️ {error_handling}\n"
        comment += "\n"
        
        comment += f"━━━━━━━━━━━━━━━━━━━━\n\n"
    
    comment += f"🐍 Python Compatibility\n\n"
    
    comment += f"Python {summary.get('baseline_version', '3.11')} — Baseline\n"
    baseline_pass = summary.get('baseline_pass', 0)
    baseline_total = len(baseline)
    if baseline_pass == baseline_total and baseline_total > 0:
        comment += f"✅ PASS ({baseline_pass}/{baseline_total})\n\n"
    elif baseline_total == 0:
        comment += f"⏭️ SKIPPED\n\n"
    else:
        comment += f"❌ FAIL ({baseline_pass}/{baseline_total})\n\n"
    
    comment += f"Python {summary.get('latest_version', '3.12')} — Latest\n"
    latest_pass = summary.get('latest_pass', 0)
    latest_total = len(latest)
    if latest_pass == latest_total and latest_total > 0:
        comment += f"✅ PASS ({latest_pass}/{latest_total})\n\n"
    elif latest_total == 0:
        comment += f"⏭️ SKIPPED\n\n"
    else:
        comment += f"❌ FAIL ({latest_pass}/{latest_total})\n\n"
    
    comment += f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    
    # Final result
    total_pass = baseline_pass + latest_pass
    total_tests = baseline_total + latest_total
    
    if total_pass == total_tests and total_tests > 0:
        comment += "🎯 RESULT: ✅ PASSED\n\n"
    elif total_tests == 0:
        comment += "🎯 RESULT: ⏭️ SKIPPED\n\n"
    else:
        comment += "🎯 RESULT: ❌ FAILED\n\n"
    
    return comment

def find_existing_comment(pr_number, repo, token):
    import requests
    
    url = f"https://api.github.com/repos/{repo}/issues/{pr_number}/comments"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        return None
    
    comments = response.json()
    for comment in comments:
        if COMMENT_MARKER in comment.get("body", ""):
            return comment
    
    return None

def post_pr_comment(comment):
    import requests
    
    pr_number = os.environ.get("PR_NUMBER")
    repo = os.environ.get("GITHUB_REPOSITORY")
    token = os.environ.get("GITHUB_TOKEN")
    
    if not all([pr_number, repo, token]):
        print("Missing required environment variables")
        return
    
    existing_comment = find_existing_comment(pr_number, repo, token)
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    if existing_comment:
        comment_id = existing_comment["id"]
        url = f"https://api.github.com/repos/{repo}/issues/comments/{comment_id}"
        response = requests.patch(url, json={"body": comment}, headers=headers)
        if response.status_code in [200, 201]:
            print("PR comment updated successfully")
        else:
            print(f"Failed to update comment: {response.status_code}")
            print(response.text)
    else:
        url = f"https://api.github.com/repos/{repo}/issues/{pr_number}/comments"
        response = requests.post(url, json={"body": comment}, headers=headers)
        if response.status_code in [200, 201]:
            print("PR comment posted successfully")
        else:
            print(f"Failed to post comment: {response.status_code}")
            print(response.text)

if __name__ == "__main__":
    results_file = "final-runtime-results.json"
    comment = generate_pr_comment(results_file)
    post_pr_comment(comment)
