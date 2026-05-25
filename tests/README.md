# Plugin-Tests

Dieser Ordner enthält Tests für alle Plugins im Marketplace. Die Tests werden automatisch bei Pull Requests ausgeführt.

## Test-Kategorien

### test_plugin_structure.py
Prüft die grundlegende Struktur aller Plugins:
- Jeder Plugin-Ordner muss eine `plugin.json` haben
- `plugin.json` muss gültiges JSON sein
- Alle Pflichtfelder müssen vorhanden sein
- Plugin-Name und Version Format prüfen
- Ordner-Namenskonventionen (lowercase, keine Leerzeichen)

### test_plugin_permissions.py
Prüft die Permissions in `plugin.json`:
- Alle Permissions müssen gültig sein
- Permissions muss eine Liste sein
- Verifizierte Plugins sollten mehr Permissions haben

### test_plugin_verified.py
Prüft das `verified` Feld und Autor-Informationen:
- `verified` muss boolean sein
- Verifizierte Plugins müssen von Gamerhund/Jonas sein
- `author` und `description` dürfen nicht leer sein

### test_plugin_files.py
Prüft optionale Dateien:
- `backend.py` muss gültiges Python sein (falls vorhanden)
- `backend.py` muss `plugin_blueprint` definieren
- `frontend.js` darf nicht leer sein (falls vorhanden)

## Tests ausführen

```bash
# Alle Tests ausführen
pytest marketplace/tests/

# Nur Struktur-Tests
pytest marketplace/tests/test_plugin_structure.py

# Mit Detail-Ausgabe
pytest marketplace/tests/ -v

# Mit Coverage
pytest marketplace/tests/ --cov=plugins
```

## CI/CD Integration

Diese Tests werden automatisch bei jedem Pull Request ausgeführt. Wenn ein Test fehlschlägt, wird der PR nicht gemerged.
