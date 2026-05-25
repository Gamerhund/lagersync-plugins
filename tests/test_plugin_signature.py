#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Plugin-Signatur Tests
Prüft ob die plugin.sig Dateien vorhanden sind und gültig sind
"""

import pytest
import json
import base64
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey


def test_verified_plugins_have_signature(plugin_dir):
    """Verifizierte Plugins müssen eine plugin.sig Datei haben"""
    for plugin_path in plugin_dir.iterdir():
        if plugin_path.is_dir() and not plugin_path.name.startswith("__"):
            plugin_json = plugin_path / "plugin.json"
            plugin_sig = plugin_path / "plugin.sig"
            
            with open(plugin_json, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if data.get("verified"):
                assert plugin_sig.exists(), \
                    f"Plugin {plugin_path.name}: Verifizierte Plugins müssen eine plugin.sig haben"


def test_signature_is_valid(plugin_dir, plugin_public_key):
    """plugin.sig muss eine gültige Ed25519 Signatur sein"""
    public_key = Ed25519PublicKey.from_public_bytes(
        base64.b64decode(plugin_public_key)
    )
    
    for plugin_path in plugin_dir.iterdir():
        if plugin_path.is_dir() and not plugin_path.name.startswith("__"):
            plugin_json = plugin_path / "plugin.json"
            plugin_sig = plugin_path / "plugin.sig"
            
            if plugin_sig.exists():
                # plugin.json lesen
                with open(plugin_json, 'r', encoding='utf-8') as f:
                    plugin_data = json.load(f)
                
                # plugin.json als String für Verifikation (gleich wie beim Signieren)
                plugin_json_str = json.dumps(plugin_data, sort_keys=True, separators=(',', ':'))
                
                # Signatur lesen
                with open(plugin_sig, 'r', encoding='utf-8') as f:
                    signature_b64 = f.read()
                
                signature = base64.b64decode(signature_b64)
                
                # Signatur verifizieren
                try:
                    public_key.verify(signature, plugin_json_str.encode('utf-8'))
                except Exception as e:
                    pytest.fail(f"Plugin {plugin_path.name}: Ungültige Signatur: {e}")


def test_signature_format(plugin_dir):
    """plugin.sig muss base64-codiert sein"""
    for plugin_path in plugin_dir.iterdir():
        if plugin_path.is_dir() and not plugin_path.name.startswith("__"):
            plugin_sig = plugin_path / "plugin.sig"
            
            if plugin_sig.exists():
                with open(plugin_sig, 'r', encoding='utf-8') as f:
                    signature_b64 = f.read()
                
                # Prüfen ob es gültiges base64 ist
                try:
                    base64.b64decode(signature_b64)
                except Exception as e:
                    pytest.fail(f"Plugin {plugin_path.name}: plugin.sig ist kein gültiges base64: {e}")
