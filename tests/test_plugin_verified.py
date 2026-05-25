#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Plugin-Verified Tests
Prüft das verified Feld und die Autor-Informationen
"""

import pytest
import json
from pathlib import Path


def test_verified_field_is_boolean(plugin_dir):
    """verified Feld muss boolean sein"""
    for plugin_path in plugin_dir.iterdir():
        if plugin_path.is_dir() and not plugin_path.name.startswith("__"):
            plugin_json = plugin_path / "plugin.json"
            with open(plugin_json, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            verified = data.get("verified")
            assert isinstance(verified, bool), \
                f"Plugin {plugin_path.name}: verified muss boolean sein, ist {type(verified)}"


def test_verified_plugins_have_author(plugin_dir):
    """Verifizierte Plugins müssen einen Autor haben"""
    for plugin_path in plugin_dir.iterdir():
        if plugin_path.is_dir() and not plugin_path.name.startswith("__"):
            plugin_json = plugin_path / "plugin.json"
            with open(plugin_json, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if data.get("verified"):
                author = data.get("author", "")
                assert author, \
                    f"Plugin {plugin_path.name}: Verifizierte Plugins müssen einen Autor haben"


def test_author_field_not_empty(plugin_dir):
    """author Feld darf nicht leer sein"""
    for plugin_path in plugin_dir.iterdir():
        if plugin_path.is_dir() and not plugin_path.name.startswith("__"):
            plugin_json = plugin_path / "plugin.json"
            with open(plugin_json, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            author = data.get("author", "")
            assert author, f"Plugin {plugin_path.name}: author darf nicht leer sein"
            assert len(author) > 0, f"Plugin {plugin_path.name}: author darf nicht leer sein"


def test_description_field_not_empty(plugin_dir):
    """description Feld darf nicht leer sein"""
    for plugin_path in plugin_dir.iterdir():
        if plugin_path.is_dir() and not plugin_path.name.startswith("__"):
            plugin_json = plugin_path / "plugin.json"
            with open(plugin_json, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            description = data.get("description", "")
            assert description, f"Plugin {plugin_path.name}: description darf nicht leer sein"
            assert len(description) > 0, f"Plugin {plugin_path.name}: description darf nicht leer sein"
