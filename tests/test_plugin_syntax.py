#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Plugin-Syntax Tests

Prüft ob alle backend.py und frontend.js Dateien syntaktisch fehlerfrei sind.
Syntaxfehler in diesen Dateien würden das Laden des Plugins im Produktionssystem
komplett verhindern.
"""

import py_compile
import shutil
import subprocess
import pytest
from pathlib import Path


def test_python_syntax(plugin_dir):
    """
    Alle backend.py Dateien müssen syntaktisch korrekt sein.

    Ein Syntaxfehler in backend.py verhindert das Laden des Plugins und führt
    zu einem ImportError / SyntaxError beim Start.
    """
    for plugin_path in plugin_dir.iterdir():
        if not plugin_path.is_dir() or plugin_path.name.startswith("__"):
            continue
        backend = plugin_path / "backend.py"
        if not backend.exists():
            continue
        try:
            py_compile.compile(str(backend), doraise=True)
        except py_compile.PyCompileError as e:
            pytest.fail(
                f"\n\n"
                f"  ❌  Syntaxfehler in '{plugin_path.name}/backend.py':\n\n"
                f"  {e}\n\n"
                f"  Das Plugin kann nicht geladen werden bis der Fehler behoben ist.\n"
            )


def test_javascript_syntax(plugin_dir):
    """
    Alle frontend.js Dateien müssen syntaktisch korrekt sein (node --check).

    Ein Syntaxfehler in frontend.js führt dazu, dass das Script im Browser
    gar nicht ausgeführt wird und das Plugin UI komplett fehlt.

    Voraussetzung: Node.js muss installiert sein. Fehlt Node.js, wird der
    Test übersprungen (skip) – kein Fehler.
    """
    node = shutil.which("node")
    if not node:
        pytest.skip("Node.js nicht verfügbar – JavaScript-Syntaxprüfung übersprungen")

    for plugin_path in plugin_dir.iterdir():
        if not plugin_path.is_dir() or plugin_path.name.startswith("__"):
            continue
        frontend = plugin_path / "frontend.js"
        if not frontend.exists():
            continue
        result = subprocess.run(
            [node, "--check", str(frontend)],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            pytest.fail(
                f"\n\n"
                f"  ❌  Syntaxfehler in '{plugin_path.name}/frontend.js':\n\n"
                f"  {result.stderr.strip()}\n\n"
                f"  Das Plugin-Frontend wird im Browser nicht ausgeführt bis der Fehler behoben ist.\n"
            )
