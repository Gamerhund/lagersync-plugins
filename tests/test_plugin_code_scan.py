#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Plugin-Code-Scanner Tests

Spiegelt exakt die Logik von plugin_security.py::scan_plugin_code().
Wenn sich die Muster in plugin_security.py aendern, muessen sie hier
aktualisiert werden (DANGEROUS_PATTERNS unten).

Plugins die hier fehlschlagen wuerden im Produktionssystem Warnungen
ausloesen oder geblockt werden.
"""

import re
import json
import pytest
from pathlib import Path


# Exakt die gleichen Muster wie plugin_security.py::scan_plugin_code()
DANGEROUS_PATTERNS = [
    (r"os\.system\s*\(",   "os.system() - Befehlsausfuehrung",         "high"),
    (r"subprocess\.",       "subprocess - Prozessausfuehrung",           "high"),
    (r"eval\s*\(",          "eval() - Code-Ausfuehrung",                 "high"),
    (r"exec\s*\(",          "exec() - Code-Ausfuehrung",                 "high"),
    (r"__import__\s*\(",    "__import__() - Dynamischer Import",         "high"),
    (r"socket\.",           "socket - Direkter Netzwerkzugriff",         "medium"),
    (r"open\s*\([^)]*\.\.", "open('../') - Pfad-Traversal",              "medium"),
    (r"shutil\.rmtree",     "shutil.rmtree - Rekursives Loeschen",       "medium"),
    (r"import\s+pickle",    "pickle - Unsichere Deserialisierung (RCE)", "medium"),
]

SCAN_FILES = ["backend.py", "frontend.js"]


def _scan_file(filepath):
    """Scannt eine Datei auf gefaehrliche Muster."""
    if not filepath.exists():
        return []
    findings = []
    try:
        content = filepath.read_text(encoding="utf-8", errors="ignore")
        for pattern, message, severity in DANGEROUS_PATTERNS:
            if re.search(pattern, content):
                findings.append({
                    "file": filepath.name,
                    "pattern": pattern,
                    "message": message,
                    "severity": severity,
                })
    except Exception as e:
        findings.append({"file": filepath.name, "message": f"Scan-Fehler: {e}", "severity": "low"})
    return findings


def test_no_high_severity_patterns(plugin_dir):
    """
    Kein Plugin darf high-severity Muster enthalten.
    Diese werden vom Produktionssystem (plugin_security.py) erkannt und
    erzeugen einen Security-Check-Fehler beim Laden:
    os.system, subprocess, eval, exec, __import__
    """
    for plugin_path in plugin_dir.iterdir():
        if not plugin_path.is_dir() or plugin_path.name.startswith("__"):
            continue
        for fname in SCAN_FILES:
            findings = [f for f in _scan_file(plugin_path / fname) if f["severity"] == "high"]
            lines = ["  - " + f["message"] for f in findings]
            assert not findings, (
                f"\n\n  Gefaehrliches Muster in '{plugin_path.name}' ({fname}):\n"
                + "\n".join(lines)
                + "\n\n  Diese Muster blockieren das Plugin. Verwende die Plugin-APIs.\n"
            )


def test_no_medium_severity_patterns(plugin_dir):
    """
    Plugins sollten keine medium-severity Muster enthalten.
    Diese erzeugen Warnungen im Produktionssystem:
    socket, pickle, shutil.rmtree, Pfad-Traversal

    Fuer Netzwerkzugriff: 'system.network' Permission + PluginAPI.fetch() nutzen.
    """
    for plugin_path in plugin_dir.iterdir():
        if not plugin_path.is_dir() or plugin_path.name.startswith("__"):
            continue
        for fname in SCAN_FILES:
            findings = [f for f in _scan_file(plugin_path / fname) if f["severity"] == "medium"]
            lines = ["  - " + f["message"] for f in findings]
            assert not findings, (
                f"\n\n  Verdaechtiges Muster in '{plugin_path.name}' ({fname}):\n"
                + "\n".join(lines)
                + "\n\n  Netzwerkzugriff: PluginAPI.fetch() (Frontend) oder\n"
                + "  das injizierte requests-Objekt (Backend) nutzen.\n"
            )


def test_socket_requires_network_permission(plugin_dir):
    """
    Ein Plugin das socket im Code verwendet muss die 'system.network'
    Permission explizit anfordern. Ohne sie wird der Zugriff blockiert.
    """
    for plugin_path in plugin_dir.iterdir():
        if not plugin_path.is_dir() or plugin_path.name.startswith("__"):
            continue
        backend = plugin_path / "backend.py"
        if not backend.exists():
            continue
        content = backend.read_text(encoding="utf-8", errors="ignore")
        if re.search(r"socket\.", content):
            plugin_json = plugin_path / "plugin.json"
            with open(plugin_json, "r", encoding="utf-8") as f:
                data = json.load(f)
            assert "system.network" in data.get("permissions", []), (
                f"Plugin {plugin_path.name}: Nutzt 'socket' aber hat keine "
                f"'system.network' Permission in plugin.json"
            )


def test_no_hardcoded_real_secrets(plugin_dir):
    """
    Plugins duerfen keine echten hardcodierten Secrets enthalten.
    Gepruefte Formate: Slack-Tokens, Telegram-Bot-Tokens, OpenAI-Keys,
    GitHub-Tokens, Google-API-Keys.
    DB-Schluesselkonstanten wie _KEY = "keyname" werden NICHT markiert.
    Echte Secrets ueber get_setting_value() aus der Settings-Tabelle laden.
    """
    real_secret_patterns = [
        (r"xox[bpra]-[0-9A-Za-z\-]{10,}",  "Slack-Token"),
        (r"[0-9]{8,10}:[A-Za-z0-9_\-]{35,}", "Telegram-Bot-Token"),
        (r"sk-[A-Za-z0-9]{32,}",             "OpenAI API-Key"),
        (r"ghp_[A-Za-z0-9]{36}",             "GitHub Personal Access Token"),
        (r"AIza[0-9A-Za-z\-_]{35}",          "Google API-Key"),
    ]
    for plugin_path in plugin_dir.iterdir():
        if not plugin_path.is_dir() or plugin_path.name.startswith("__"):
            continue
        for fname in SCAN_FILES:
            filepath = plugin_path / fname
            if not filepath.exists():
                continue
            file_content = filepath.read_text(encoding="utf-8", errors="ignore")
            for pattern, label in real_secret_patterns:
                assert not re.search(pattern, file_content), (
                    f"Plugin {plugin_path.name} - {fname}: Echtes {label}-Format erkannt!\n"
                    f"  Keine echten Secrets in Code speichern.\n"
                    f"  Nutze get_setting_value() um Secrets aus der Settings-Tabelle zu lesen."
                )
