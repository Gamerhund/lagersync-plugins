#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PR Review Analyzer - Plugin Marketplace
Liest pytest-report.json und postet einen formatierten Kommentar im PR.
Basiert auf dem gleichen Konzept wie der Analyzer im LagerSync-Hauptrepo.
"""

import json
import os
from pathlib import Path

try:
    import requests
except ImportError:
    os.system("pip install requests -q")
    import requests


# Test-Kategorien mit Anzeigenamen und Emojis
TEST_CATEGORIES = {
    "test_plugin_structure":  ("📁 Struktur",       "Ordnerstruktur & plugin.json Felder"),
    "test_plugin_verified":   ("✅ Verified",        "verified-Feld & Autor-Angaben"),
    "test_plugin_permissions":("🔑 Permissions",    "Berechtigungen"),
    "test_plugin_files":      ("📄 Dateien",         "backend.py & frontend.js"),
    "test_plugin_code_scan":  ("🔒 Code-Scanner",   "Gefährliche Muster & Secrets"),
    "test_plugin_signature":  ("🖊️ Signatur",       "Ed25519 Signaturen"),
}


def load_report(filepath="pytest-report.json"):
    try:
        if Path(filepath).exists():
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception as e:
        print(f"Fehler beim Laden des Reports: {e}")
    return None


def categorize_tests(report):
    """Gruppiert Tests nach Datei/Kategorie."""
    categories = {}
    for test in report.get("tests", []):
        node_id = test.get("nodeid", "")
        # tests/test_plugin_files.py::test_name -> test_plugin_files
        parts = node_id.split("::")
        if len(parts) >= 2:
            file_part = Path(parts[0]).stem  # test_plugin_files
            if file_part not in categories:
                categories[file_part] = {"passed": [], "failed": [], "error": []}
            outcome = test.get("outcome", "unknown")
            if outcome == "passed":
                categories[file_part]["passed"].append(test)
            elif outcome == "failed":
                categories[file_part]["failed"].append(test)
            else:
                categories[file_part]["error"].append(test)
    return categories


def extract_failure_message(test):
    """Extrahiert die relevante Fehlermeldung aus einem fehlgeschlagenen Test."""
    longrepr = test.get("call", {}).get("longrepr", "")
    if not longrepr:
        longrepr = test.get("longrepr", "")

    # Nur die AssertionError-Zeile extrahieren, nicht den ganzen Traceback
    lines = str(longrepr).split("\n")
    msg_lines = []
    for line in lines:
        stripped = line.strip()
        # Relevante Zeilen: AssertionError, E-Zeilen, ❌ Zeilen
        if (stripped.startswith("E ") or
                "AssertionError" in stripped or
                "❌" in stripped or
                "⚠️" in stripped or
                "Fix:" in stripped):
            clean = stripped.lstrip("E ").strip()
            if clean and clean not in msg_lines:
                msg_lines.append(clean)
    return "\n".join(msg_lines[:6]) if msg_lines else str(longrepr)[:200]


def format_comment(report, categories):
    """Formatiert den PR-Kommentar."""
    summary = report.get("summary", {})
    total   = summary.get("total", 0)
    passed  = summary.get("passed", 0)
    failed  = summary.get("failed", 0)
    errors  = summary.get("error", 0)

    all_ok = (failed + errors) == 0

    comment = "## 🧩 Plugin Tests – PR Review\n\n"

    # Gesamtstatus
    if all_ok:
        comment += f"✅ **Alle {total} Tests bestanden** – Plugin ist marketplace-ready!\n\n"
    else:
        bad = failed + errors
        comment += (
            f"❌ **{bad} von {total} Tests fehlgeschlagen** – "
            f"Bitte vor dem Merge beheben.\n\n"
        )

    # Tabelle pro Kategorie
    comment += "### Ergebnisse nach Kategorie\n\n"
    comment += "| Kategorie | Status | Tests |\n"
    comment += "|-----------|--------|-------|\n"

    for file_key, (label, desc) in TEST_CATEGORIES.items():
        cat = categories.get(file_key, {})
        n_pass  = len(cat.get("passed", []))
        n_fail  = len(cat.get("failed", []))
        n_err   = len(cat.get("error", []))
        n_total = n_pass + n_fail + n_err

        if n_total == 0:
            status = "⚪ –"
            detail = "keine Tests"
        elif n_fail + n_err == 0:
            status = "✅ Bestanden"
            detail = f"{n_pass}/{n_total}"
        else:
            status = f"❌ **{n_fail + n_err} Fehler**"
            detail = f"{n_pass}/{n_total}"

        comment += f"| {label} – {desc} | {status} | {detail} |\n"

    # Fehlerdetails
    has_failures = any(
        len(categories.get(k, {}).get("failed", [])) > 0 or
        len(categories.get(k, {}).get("error", [])) > 0
        for k in categories
    )

    if has_failures:
        comment += "\n### ❌ Fehlgeschlagene Tests\n\n"
        for file_key, cat in categories.items():
            bad_tests = cat.get("failed", []) + cat.get("error", [])
            if not bad_tests:
                continue
            label = TEST_CATEGORIES.get(file_key, ("", ""))[0]
            comment += f"#### {label} (`{file_key}`)\n\n"
            for test in bad_tests:
                name = test.get("nodeid", "").split("::")[-1]
                msg  = extract_failure_message(test)
                comment += f"**`{name}`**\n"
                if msg:
                    comment += f"```\n{msg}\n```\n"
                comment += "\n"

    # Schnelle Hilfe wenn verified-Fehler
    if "test_plugin_verified" in categories:
        vf = categories["test_plugin_verified"].get("failed", [])
        for t in vf:
            if "self_verify" in t.get("nodeid", ""):
                comment += (
                    "\n> 💡 **Tipp:** `verified` darf nicht selbst auf `true` gesetzt werden.\n"
                    "> Setze `\"verified\": false` – der Maintainer setzt es nach Prüfung.\n"
                )
                break

    comment += (
        "\n---\n"
        "*Automatisch generiert von Plugin Tests CI · "
        "[lagersync-plugins](https://github.com/Gamerhund/lagersync-plugins)*"
    )
    return comment


def post_comment(comment):
    """Postet den Kommentar als GitHub PR Comment."""
    pr_number = os.environ.get("PR_NUMBER")
    token     = os.environ.get("GITHUB_TOKEN")
    repo      = os.environ.get("GITHUB_REPOSITORY")

    if not all([pr_number, token, repo]):
        print("Fehlende Umgebungsvariablen (PR_NUMBER, GITHUB_TOKEN, GITHUB_REPOSITORY)")
        return False

    url = f"https://api.github.com/repos/{repo}/issues/{pr_number}/comments"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
    }

    try:
        resp = requests.post(url, headers=headers, json={"body": comment}, timeout=30)
        if resp.status_code == 201:
            print("✅ Kommentar erfolgreich gepostet")
            return True
        else:
            print(f"Fehler: HTTP {resp.status_code} – {resp.text[:200]}")
            return False
    except Exception as e:
        print(f"Fehler beim Posten: {e}")
        return False


def main():
    print("Starte Plugin PR-Review-Analyse...")

    report = load_report("pytest-report.json")
    if not report:
        print("pytest-report.json nicht gefunden – kein Kommentar gepostet")
        return

    categories = categorize_tests(report)
    comment    = format_comment(report, categories)

    print(comment)
    print("\n--- Poste Kommentar ---")
    post_comment(comment)


if __name__ == "__main__":
    main()
