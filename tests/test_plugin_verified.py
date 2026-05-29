#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Plugin-Verified Tests
Prüft das verified Feld und die Autor-Informationen
"""

import pytest
import json
from pathlib import Path
try:
    from conftest import MAINTAINER_VERIFIED_PLUGINS
except ModuleNotFoundError:
    MAINTAINER_VERIFIED_PLUGINS = frozenset([
        "ki-assistent",
        "low_stock_notifications",
        "pro-design",
    ])


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

def test_new_plugins_must_not_self_verify(plugin_dir):
    """
    Neue Plugins dürfen verified NICHT auf true setzen.

    Das Feld wird ausschließlich vom Maintainer gesetzt – nach persönlicher
    Prüfung des Quellcodes. Plugin-Entwickler müssen 'verified: false' lassen.
    Das Plugin erscheint dann zunächst ohne Badge im Marketplace – das ist normal.
    """
    for plugin_path in plugin_dir.iterdir():
        if plugin_path.is_dir() and not plugin_path.name.startswith("__"):

            # Bereits offiziell verifizierte Plugins überspringen
            if plugin_path.name in MAINTAINER_VERIFIED_PLUGINS:
                continue

            plugin_json = plugin_path / "plugin.json"
            with open(plugin_json, 'r', encoding='utf-8') as f:
                data = json.load(f)

            verified = data.get("verified")
            assert verified is False, (
                f"\n\n"
                f"  ❌  Plugin '{plugin_path.name}': verified darf nicht auf true gesetzt werden!\n"
                f"\n"
                f"  Das Feld wird ausschließlich vom Maintainer nach persönlicher\n"
                f"  Prüfung des Quellcodes gesetzt. Dein Plugin erscheint zunächst\n"
                f"  ohne Verified-Badge im Marketplace – das ist völlig normal.\n"
                f"\n"
                f"  Fix: Setze in deiner plugin.json:\n"
                f'       "verified": false\n'
            )
