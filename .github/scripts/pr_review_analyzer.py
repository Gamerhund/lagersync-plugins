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

# ── Auto-Labels ──────────────────────────────────────────────────────────
# Bewusst klein gehalten: zwei Achsen (risk/type), je 3-4 Werte, keine
# 20 verschiedenen Tags. Ziel ist ein Blick auf die PR-Liste reicht, nicht
# ein eigenes Ranking-System.
LABEL_DEFS = {
    "risk: high":   "d73a4a",  # rot
    "risk: medium": "fbca04",  # gelb
    "risk: low":    "0e8a16",  # gruen
    "type: feature":"0366d6",  # blau   - neues Plugin
    "type: update": "5319e7",  # lila   - bestehendes Plugin geaendert
    "type: docs":   "0075ca",  # hellblau
    "type: chore":  "cfd3d7",  # grau   - nur CI/Tests/Tooling
    "type: other":  "ededed",  # hellgrau - Mischung, nicht eindeutig
}

# Muster, die im Diff-Patch-Text auf riskanten Code hindeuten - bewusst eine
# kleine Teilmenge von tests/test_plugin_code_scan.py, nur fuer die grobe
# Einschaetzung hier, ersetzt den eigentlichen Scanner-Test nicht.
RISKY_PATCH_PATTERNS = [
    "os.system(", "subprocess.", "eval(", "exec(", "__import__(",
    "socket.", "pickle.", "shutil.rmtree", "../",
]

HIGH_RISK_PERMISSIONS = {"db.write", "api.admin", "system.network"}


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

    if all_ok:
        comment += f"✅ **Alle {total} Tests bestanden** – Plugin ist marketplace-ready!\n\n"
    else:
        bad = failed + errors
        comment += (
            f"❌ **{bad} von {total} Tests fehlgeschlagen** – "
            f"Bitte vor dem Merge beheben.\n\n"
        )

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


def get_pr_files(repo, pr_number, headers):
    """Holt alle geänderten Dateien des PR über die GitHub API (mit Pagination)."""
    files = []
    page = 1
    while True:
        url = f"https://api.github.com/repos/{repo}/pulls/{pr_number}/files"
        try:
            resp = requests.get(url, headers=headers, params={"per_page": 100, "page": page}, timeout=30)
            if resp.status_code != 200:
                print(f"PR-Files Fehler: HTTP {resp.status_code}")
                break
            batch = resp.json()
            files.extend(batch)
            if len(batch) < 100:
                break
            page += 1
        except Exception as e:
            print(f"PR-Files Fehler: {e}")
            break
    return files


def classify_type(files):
    """Grobe Einordnung: neues Plugin / bestehendes geändert / nur Doku / nur Tooling / Mischung."""
    paths = [f["filename"] for f in files]
    plugin_paths   = [p for p in paths if p.startswith("plugins/")]
    new_plugin_jsons = [
        f for f in files
        if f["filename"].startswith("plugins/") and f["filename"].endswith("/plugin.json")
        and f.get("status") == "added"
    ]
    only_docs   = all(p.endswith(".md") or p.startswith("docs/") for p in paths) if paths else False
    only_chore  = all(p.startswith(".github/") or p.startswith("tests/") for p in paths) if paths else False

    if new_plugin_jsons:
        return "type: feature"
    if plugin_paths:
        return "type: update"
    if only_docs:
        return "type: docs"
    if only_chore:
        return "type: chore"
    return "type: other"


def classify_risk(files):
    """
    Grobe Risiko-Einschätzung für die erste Sichtung - ersetzt nicht den
    echten Code-Scanner-Test, sondern gibt nur eine schnelle Einordnung,
    bevor man überhaupt reinguckt.
    """
    high_signals = []
    medium_signals = []

    for f in files:
        path = f["filename"]
        patch = f.get("patch", "") or ""

        if path.startswith(".github/workflows/"):
            high_signals.append(f"CI/Workflow geändert: {path}")
        if path == "docs/SECURITY.md" or path.endswith("tenant_middleware.py"):
            high_signals.append(f"Sicherheitsrelevante Datei: {path}")
        for pattern in RISKY_PATCH_PATTERNS:
            if pattern in patch:
                high_signals.append(f"Verdächtiges Muster `{pattern}` im Diff von {path}")
                break

        if path.endswith("plugin.json"):
            added_lines = "\n".join(
                line for line in patch.splitlines() if line.startswith("+") and not line.startswith("+++")
            )
            for perm in HIGH_RISK_PERMISSIONS:
                if perm in added_lines:
                    high_signals.append(f"Neue Permission `{perm}` in {path}")
        if path.endswith("backend.py"):
            medium_signals.append(f"backend.py geändert: {path}")

    if high_signals:
        return "risk: high", high_signals
    if medium_signals:
        return "risk: medium", medium_signals
    return "risk: low", []


def ensure_labels_exist(repo, headers):
    """Legt fehlende Labels einmalig an (Farbe egal beim erneuten Aufruf, 422 = existiert schon = ok)."""
    for name, color in LABEL_DEFS.items():
        url = f"https://api.github.com/repos/{repo}/labels"
        try:
            resp = requests.post(url, headers=headers, json={"name": name, "color": color}, timeout=15)
            if resp.status_code not in (201, 422):
                print(f"Label '{name}' anlegen: HTTP {resp.status_code} – {resp.text[:120]}")
        except Exception as e:
            print(f"Label '{name}' anlegen fehlgeschlagen: {e}")


def apply_labels(repo, pr_number, headers, risk_label, type_label):
    """
    Setzt risk:/type:-Label neu, ohne andere (z.B. manuell gesetzte) Labels
    anzufassen. Entfernt zuerst alte risk:/type:-Werte, falls ein Folge-Commit
    die Einschätzung verändert hat (sonst bleiben alte UND neue gleichzeitig kleben).
    """
    issue_url = f"https://api.github.com/repos/{repo}/issues/{pr_number}"

    try:
        resp = requests.get(issue_url, headers=headers, timeout=15)
        current = [l["name"] for l in resp.json().get("labels", [])] if resp.status_code == 200 else []
    except Exception:
        current = []

    stale = [l for l in current if l.startswith("risk: ") or l.startswith("type: ")]
    for label in stale:
        if label in (risk_label, type_label):
            continue
        try:
            requests.delete(f"{issue_url}/labels/{requests.utils.quote(label)}", headers=headers, timeout=15)
        except Exception as e:
            print(f"Altes Label '{label}' entfernen fehlgeschlagen: {e}")

    try:
        resp = requests.post(f"{issue_url}/labels", headers=headers,
                              json={"labels": [risk_label, type_label]}, timeout=15)
        if resp.status_code == 200:
            print(f"✅ Labels gesetzt: {risk_label}, {type_label}")
        else:
            print(f"Labels setzen: HTTP {resp.status_code} – {resp.text[:150]}")
    except Exception as e:
        print(f"Labels setzen fehlgeschlagen: {e}")


def run_auto_labeling(repo, pr_number, headers):
    files = get_pr_files(repo, pr_number, headers)
    if not files:
        print("Keine PR-Dateien gefunden, überspringe Auto-Labeling.")
        return
    type_label = classify_type(files)
    risk_label, signals = classify_risk(files)
    print(f"Auto-Label: {risk_label} / {type_label}")
    for s in signals:
        print(f"  - {s}")
    ensure_labels_exist(repo, headers)
    apply_labels(repo, pr_number, headers, risk_label, type_label)


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

    pr_number = os.environ.get("PR_NUMBER")
    token     = os.environ.get("GITHUB_TOKEN")
    repo      = os.environ.get("GITHUB_REPOSITORY")
    if all([pr_number, token, repo]):
        print("\n--- Auto-Labeling ---")
        headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json",
        }
        run_auto_labeling(repo, pr_number, headers)


if __name__ == "__main__":
    main()
