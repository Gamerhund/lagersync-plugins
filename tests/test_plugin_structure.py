#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Plugin-Struktur Tests
Prüft ob alle Plugins die korrekte Struktur haben
"""

import pytest
import json
from pathlib import Path


def test_all_plugins_have_plugin_json(plugin_dir):
    """Jeder Plugin-Ordner muss eine plugin.json haben"""
    for plugin_path in plugin_dir.iterdir():
        if plugin_path.is_dir() and not plugin_path.name.startswith("__"):
            plugin_json = plugin_path / "plugin.json"
            assert plugin_json.exists(), f"Plugin {plugin_path.name} hat keine plugin.json"


def test_plugin_json_valid_json(plugin_dir):
    """plugin.json muss gültiges JSON sein"""
    for plugin_path in plugin_dir.iterdir():
        if plugin_path.is_dir() and not plugin_path.name.startswith("__"):
            plugin_json = plugin_path / "plugin.json"
            with open(plugin_json, 'r', encoding='utf-8') as f:
                try:
                    json.load(f)
                except json.JSONDecodeError as e:
                    pytest.fail(f"plugin.json in {plugin_path.name} ist kein gültiges JSON: {e}")


def test_plugin_json_required_fields(plugin_dir):
    """plugin.json muss alle Pflichtfelder haben"""
    required_fields = ["name", "version", "author", "description", "verified", "enabled"]
    
    for plugin_path in plugin_dir.iterdir():
        if plugin_path.is_dir() and not plugin_path.name.startswith("__"):
            plugin_json = plugin_path / "plugin.json"
            with open(plugin_json, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            for field in required_fields:
                assert field in data, f"Plugin {plugin_path.name}: Pflichtfeld '{field}' fehlt"


def test_plugin_name_not_empty(plugin_dir):
    """Plugin-Name darf nicht leer sein"""
    for plugin_path in plugin_dir.iterdir():
        if plugin_path.is_dir() and not plugin_path.name.startswith("__"):
            plugin_json = plugin_path / "plugin.json"
            with open(plugin_json, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            assert data.get("name"), f"Plugin {plugin_path.name}: name ist leer"
            assert len(data.get("name", "")) > 0, f"Plugin {plugin_path.name}: name ist leer"


def test_plugin_version_format(plugin_dir):
    """Plugin-Version muss Semantic Versioning Format haben (X.Y.Z)"""
    import re
    
    for plugin_path in plugin_dir.iterdir():
        if plugin_path.is_dir() and not plugin_path.name.startswith("__"):
            plugin_json = plugin_path / "plugin.json"
            with open(plugin_json, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            version = data.get("version", "")
            assert re.match(r'^\d+\.\d+\.\d+$', version), \
                f"Plugin {plugin_path.name}: version '{version}' hat nicht das Format X.Y.Z"


def test_plugin_folder_name_lowercase(plugin_dir):
    """Plugin-Ordnername sollte lowercase sein"""
    for plugin_path in plugin_dir.iterdir():
        if plugin_path.is_dir() and not plugin_path.name.startswith("__"):
            assert plugin_path.name == plugin_path.name.lower(), \
                f"Plugin-Ordner {plugin_path.name} sollte lowercase sein"


def test_plugin_folder_name_no_spaces(plugin_dir):
    """Plugin-Ordnername darf keine Leerzeichen haben"""
    for plugin_path in plugin_dir.iterdir():
        if plugin_path.is_dir() and not plugin_path.name.startswith("__"):
            assert " " not in plugin_path.name, \
                f"Plugin-Ordner {plugin_path.name} darf keine Leerzeichen enthalten"
