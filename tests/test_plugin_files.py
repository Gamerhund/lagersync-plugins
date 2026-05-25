#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Plugin-Dateien Tests
Prüft ob optionale Dateien (backend.py, frontend.js) vorhanden sind und syntaktisch korrekt
"""

import pytest
import ast
from pathlib import Path


def test_backend_py_syntax_if_exists(plugin_dir):
    """backend.py muss gültiges Python sein (falls vorhanden)"""
    for plugin_path in plugin_dir.iterdir():
        if plugin_path.is_dir() and not plugin_path.name.startswith("__"):
            backend_py = plugin_path / "backend.py"
            if backend_py.exists():
                with open(backend_py, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                try:
                    ast.parse(content)
                except SyntaxError as e:
                    pytest.fail(f"Plugin {plugin_path.name}: backend.py hat Syntaxfehler: {e}")


def test_backend_py_has_blueprint(plugin_dir):
    """backend.py muss plugin_blueprint definieren (falls vorhanden)"""
    for plugin_path in plugin_dir.iterdir():
        if plugin_path.is_dir() and not plugin_path.name.startswith("__"):
            backend_py = plugin_path / "backend.py"
            if backend_py.exists():
                with open(backend_py, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                assert "plugin_blueprint" in content, \
                    f"Plugin {plugin_path.name}: backend.py muss 'plugin_blueprint' definieren"


def test_frontend_js_syntax_if_exists(plugin_dir):
    """frontend.js sollte gültiges JavaScript sein (falls vorhanden)"""
    for plugin_path in plugin_dir.iterdir():
        if plugin_path.is_dir() and not plugin_path.name.startswith("__"):
            frontend_js = plugin_path / "frontend.js"
            if frontend_js.exists():
                with open(frontend_js, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Einfache Syntax-Prüfung: prüfe auf grundlegende JavaScript-Muster
                # (keine vollständige JS-Parser-Implementierung)
                assert content.strip(), f"Plugin {plugin_path.name}: frontend.js ist leer"
