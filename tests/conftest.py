#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Pytest Konfiguration für Plugin-Tests
"""

import pytest
import json
import os
import sys
from pathlib import Path

PLUGIN_DIR = Path(__file__).parent.parent / "plugins"

# Liste kommt aus .github/verified_plugins.py - das ist die einzige Stelle,
# die man beim Freigeben eines neuen Plugins anfassen muss. Diese Datei hier
# importiert nur davon, damit pytest-Tests und update_readme.py garantiert
# dieselbe Liste sehen.
sys.path.insert(0, str(Path(__file__).parent.parent / ".github"))
from verified_plugins import MAINTAINER_VERIFIED_PLUGINS  # noqa: E402

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
