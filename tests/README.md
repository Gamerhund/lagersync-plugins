# Plugin-Tests

Dieser Ordner enthält Tests für alle Plugins im Marketplace. Die Tests werden automatisch bei jedem Pull Request ausgeführt.

## Test-Kategorien

### test_plugin_structure.py
Prüft die grundlegende Struktur aller Plugins:
- Jeder Plugin-Ordner muss eine `plugin.json` haben
- `plugin.json` muss gültiges JSON sein
- Alle Pflichtfelder müssen vorhanden sein (`name`, `version`, `author`, `description`, `verified`, `enabled`)
- Version muss Semantic Versioning Format haben (X.Y.Z)
- Ordner-Namenskonventionen (lowercase, keine Leerzeichen)

### test_plugin_permissions.py
Prüft die Permissions in `plugin.json`:
- Alle Permissions müssen gültig sein (siehe PLUGINS.md für vollständige Liste)
- `permissions` muss eine Liste sein

### test_plugin_verified.py
Prüft das `verified` Feld und Autor-Informationen:
- `verified` muss boolean sein
- `author` und `description` dürfen nicht leer sein
- **Neue Plugins dürfen `verified` nicht selbst auf `true` setzen** – wird ausschließlich vom Maintainer nach persönlicher Prüfung gesetzt

### test_plugin_files.py
Prüft optionale Dateien:
- `backend.py` muss gültiges Python sein (falls vorhanden)
- `backend.py` muss `plugin_blueprint` definieren (falls vorhanden)
- `frontend.js` darf nicht leer sein (falls vorhanden)

### test_plugin_signature.py
Prüft kryptografische Signaturen:
- Verifizierte Plugins müssen eine `plugin.sig` Datei haben
- Signatur muss gültiges base64 sein
- Signatur muss mit dem offiziellen Public Key verifizierbar sein

## Tests lokal ausführen

```bash
# Alle Tests ausführen
pytest tests/ -v

# Einzelne Test-Datei
pytest tests/test_plugin_verified.py -v

# Mit kurzem Traceback
pytest tests/ -v --tb=short
```

## CI/CD

Die Tests laufen automatisch über GitHub Actions bei jedem Pull Request auf `main`. Ein PR kann nur gemerged werden wenn alle Tests bestehen.
