#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Plugins, die Jonas persoenlich geprueft und freigegeben hat.

Hier eintragen reicht. tests/conftest.py und .github/scripts/update_readme.py
importieren von hier - keine zweite Stelle mehr, die man vergessen kann.

Reihenfolge beim Freigeben eines neuen Plugins:
1. plugin.json: "verified": true setzen
2. Ed25519-Signatur (plugin.sig) erzeugen
3. Plugin-Namen hier unten eintragen
"""

MAINTAINER_VERIFIED_PLUGINS = frozenset([
    "ki-assistent",
    "low_stock_notifications",
    "pro-design",
    "sso",
])
