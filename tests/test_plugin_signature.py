#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Plugin-Signatur Tests
Prüft ob die plugin.sig Dateien vorhanden sind und gültig sind
"""

import pytest
import json
import base64
import hashlib
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
                public_key.verify(signature, plugin_json_str.encode('utf-8'))


def test_signature_format(plugin_dir):
    """plugin.sig muss base64-codiert sein"""
    for plugin_path in plugin_dir.iterdir():
        if plugin_path.is_dir() and not plugin_path.name.startswith("__"):
            plugin_sig = plugin_path / "plugin.sig"
            
            if plugin_sig.exists():
                with open(plugin_sig, 'r', encoding='utf-8') as f:
                    signature_b64 = f.read()
                
                # Prüfen ob es gültiges base64 ist
                base64.b64decode(signature_b64)


# 26.09.2026: Die Datei-Hashes in plugin.json ("files") müssen zu den Dateien passen – genau so, wie der
# LagerSync-Server prüft (plugin_security.file_digest). Vorher prüfte die CI nur die Signatur von
# plugin.json; unter Windows mit CRLF signierte Plugins waren auf dem Server deshalb „nicht gültig signiert“.
TEXT_HASH_EXTENSIONS = {'.py', '.js', '.mjs', '.cjs', '.css', '.html', '.htm', '.json', '.txt',
                        '.svg', '.yml', '.yaml', '.xml', '.csv'}
HASH_EXCLUDE = {'plugin.json', 'plugin.sig'}


def _file_digest(path):
    data = Path(path).read_bytes()
    if Path(path).suffix.lower() in TEXT_HASH_EXTENSIONS:
        data = data.replace(b'\r\n', b'\n')
    return hashlib.sha256(data).hexdigest()


def test_signed_file_hashes_match(plugin_dir):
    """Jede Code-Datei muss in plugin.json["files"] stehen und der Hash muss stimmen."""
    for plugin_path in plugin_dir.iterdir():
        if not plugin_path.is_dir() or plugin_path.name.startswith("__"):
            continue
        data = json.loads((plugin_path / "plugin.json").read_text(encoding='utf-8'))
        if not data.get("verified"):
            continue
        files = data.get("files") or {}
        assert files, f"{plugin_path.name}: plugin.json hat keine Datei-Hashes – neu signieren"
        present = sorted(
            p.relative_to(plugin_path).as_posix() for p in plugin_path.rglob('*')
            if p.is_file() and p.name not in HASH_EXCLUDE and not p.name.startswith('.')
            and not p.name.lower().endswith('.md') and '__pycache__' not in p.parts
            and not any(part.startswith('.') for part in p.relative_to(plugin_path).parts[:-1]))
        missing = [f for f in present if f not in files]
        assert not missing, f"{plugin_path.name}: nicht signierte Dateien {missing}"
        for rel, expected in files.items():
            assert '..' not in rel.split('/'), f"{plugin_path.name}: ungültiger Pfad {rel}"
            actual = _file_digest(plugin_path / rel)
            assert actual == expected, (f"{plugin_path.name}/{rel}: Hash stimmt nicht "
                                        f"(neu signieren mit aktuellem sign_plugin.py)")
