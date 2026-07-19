import py_compile
import shutil
import subprocess
import pytest
from pathlib import Path

def test_python_syntax(plugin_dir):
    for plugin_path in plugin_dir.iterdir():
        if not plugin_path.is_dir() or plugin_path.name.startswith('__'):
            continue
        backend = plugin_path / 'backend.py'
        if not backend.exists():
            continue
        try:
            py_compile.compile(str(backend), doraise=True)
        except py_compile.PyCompileError as e:
            pytest.fail(f"\n\n  ❌  Syntaxfehler in '{plugin_path.name}/backend.py':\n\n  {e}\n\n  Das Plugin kann nicht geladen werden bis der Fehler behoben ist.\n")

def test_javascript_syntax(plugin_dir):
    node = shutil.which('node')
    if not node:
        pytest.skip('Node.js nicht verfügbar – JavaScript-Syntaxprüfung übersprungen')
    for plugin_path in plugin_dir.iterdir():
        if not plugin_path.is_dir() or plugin_path.name.startswith('__'):
            continue
        frontend = plugin_path / 'frontend.js'
        if not frontend.exists():
            continue
        result = subprocess.run([node, '--check', str(frontend)], capture_output=True, text=True)
        if result.returncode != 0:
            pytest.fail(f"\n\n  ❌  Syntaxfehler in '{plugin_path.name}/frontend.js':\n\n  {result.stderr.strip()}\n\n  Das Plugin-Frontend wird im Browser nicht ausgeführt bis der Fehler behoben ist.\n")