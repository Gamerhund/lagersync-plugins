#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Pytest Konfiguration für Plugin-Tests
"""

import pytest
import json
import os
from pathlib import Path

PLUGIN_DIR = Path(__file__).parent.parent / "plugins"

# Plugins die vom Maintainer (Jonas) persönlich geprüft und freigegeben wurden.
# Nur Jonas ergänzt hier Einträge – gleichzeitig mit dem Setzen von "verified": true
# in der plugin.json und dem Hinzufügen der Ed25519-Signatur.
MAINTAINER_VERIFIED_PLUGINS = frozenset([
    "ki-assistent",
    "low_stock_notifications",
    "pro-design",
    "sso",
])

@pytest.fixture
def plugin_dir():
    """Pfad zum plugins/ Ordner"""
    return PLUGIN_DIR

@pytest.fixture
def valid_permissions():
    """Liste aller gültigen Permissions"""
    return [
        "db.read",
        "db.write",
        "inventory.read",
        "inventory.write",
        "inventory.delete",
        "users.read",
        "users.write",
        "system.settings",
        "system.files.read",
        "system.files.write",
        "system.network",
        "notifications.send",
        "api.public",
        "api.admin"
    ]

@pytest.fixture
def plugin_public_key():
    """Public Key für Plugin-Signatur-Verifikation"""
    return "lLEUuDnXSAZGt2P5CHYEg86PHgx6DGl2rGaVsznIU+c="
