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
- Alle Permissions müssen gültig sein (siehe [docs/PLUGINS.md](../docs/PLUGINS.md) für vollständige Liste)
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

### test_plugin_code_scan.py
Spiegelt die Logik des Produktions-Scanners (`plugin_security.py::scan_plugin_code()`):
- Keine high-severity Muster: `os.system()`, `subprocess`, `eval()`, `exec()`, `__import__()`
- Keine medium-severity Muster: `socket`, `pickle`, `shutil.rmtree`, Pfad-Traversal (`open('../...')`)
- Für Netzwerkzugriff stattdessen `system.network` Permission + `PluginAPI.fetch()` verwenden

### test_plugin_syntax.py
Prüft ob `backend.py` und `frontend.js` syntaktisch fehlerfrei sind:
- `backend.py` muss mit `py_compile` kompilieren
- `frontend.js` muss `node --check` bestehen (wird übersprungen, falls Node.js nicht installiert ist)

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
