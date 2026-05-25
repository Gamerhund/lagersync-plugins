#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Plugin-Permissions Tests
Prüft ob die Permissions in plugin.json gültig sind
"""

import pytest
import json
from pathlib import Path


def test_plugin_permissions_valid(plugin_dir, valid_permissions):
    """Alle Permissions in plugin.json müssen gültig sein"""
    for plugin_path in plugin_dir.iterdir():
        if plugin_path.is_dir() and not plugin_path.name.startswith("__"):
            plugin_json = plugin_path / "plugin.json"
            with open(plugin_json, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            permissions = data.get("permissions", [])
            for perm in permissions:
                assert perm in valid_permissions, \
                    f"Plugin {plugin_path.name}: Ungültige Permission '{perm}'"


def test_plugin_permissions_is_list(plugin_dir):
    """Permissions muss eine Liste sein"""
    for plugin_path in plugin_dir.iterdir():
        if plugin_path.is_dir() and not plugin_path.name.startswith("__"):
            plugin_json = plugin_path / "plugin.json"
            with open(plugin_json, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            permissions = data.get("permissions")
            assert isinstance(permissions, list), \
                f"Plugin {plugin_path.name}: permissions muss eine Liste sein"


def test_verified_plugins_have_more_permissions(plugin_dir):
    """Verifizierte Plugins sollten mehr Permissions haben als nicht-verifizierte"""
    for plugin_path in plugin_dir.iterdir():
        if plugin_path.is_dir() and not plugin_path.name.startswith("__"):
            plugin_json = plugin_path / "plugin.json"
            with open(plugin_json, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if data.get("verified"):
                permissions = data.get("permissions", [])
                assert len(permissions) > 0, \
                    f"Plugin {plugin_path.name}: Verifizierte Plugins sollten Permissions haben"
