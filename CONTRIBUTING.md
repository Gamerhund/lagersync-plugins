# 🤝 Contributing

Danke, dass du ein Plugin beitragen oder die Dokumentation verbessern willst! Dieser Ablauf gilt für beides.

## Bevor du anfängst

- Lies [docs/PLUGINS.md](docs/PLUGINS.md) (Entwickler) oder [docs/PLUGINS_KI.md](docs/PLUGINS_KI.md) (wenn eine KI den Code für dich schreibt).
- Schau in [docs/EXAMPLES.md](docs/EXAMPLES.md), ob ein ähnliches Beispiel schon existiert.
- Frage in den [Issues](https://github.com/Gamerhund/lagersync-plugins/issues), falls unklar ist, ob ein Plugin-Vorschlag ins Konzept passt.

---

## Ablauf für ein neues Plugin

1. **Fork** dieses Repository
2. **Branch erstellen**, z.B. `plugin/dein-plugin-name` (siehe Branch-Namen unten)
3. Plugin unter `plugins/dein-plugin-name/` anlegen – **nicht im Repo-Root** (dort wird nichts geladen):
   - `plugin.json` (Pflicht)
   - `backend.py` (optional)
   - `frontend.js` (optional)
4. `"verified": false` in `plugin.json` setzen – das Feld wird **ausschließlich vom Maintainer** nach persönlicher Prüfung auf `true` gesetzt
5. Optional, aber empfohlen: `description_en` in `plugin.json` ergänzen (englische Beschreibung für die englische README). Das ist nur für **neue** Plugins ohne Signatur unkompliziert – bei bereits verifizierten Plugins würde das Feld die Ed25519-Signatur invalidieren, siehe [`update_readme.py`](.github/scripts/update_readme.py)
6. Lokal testen:
   ```bash
   pip install -r requirements.txt
   pytest tests/ -v
   ```
7. **Pull Request** gegen `main` öffnen, mit kurzer Beschreibung was das Plugin macht und welche Permissions es warum braucht
8. Automatische Checks abwarten (siehe unten)
9. Nach Review wird der PR gemerged und das Plugin erscheint im Marketplace – mit **✅ Verifiziert**-Badge erst nach persönlicher Prüfung durch den Maintainer

## Ablauf für Dokumentations-Änderungen

Gleicher Fork-Branch-PR-Ablauf, nur Schritt 3–6 entfällt. Branch-Präfix `docs/`, z.B. `docs/faq-update`.

**Wichtig:** Die Plugin-Tabelle und der "X verfügbar"-Badge in `README.md`/`README_EN.md` werden automatisch aus `plugins/*/plugin.json` generiert (`.github/workflows/update-readme.yml`, läuft bei jedem Push nach `main`). Bearbeite diese Tabellen nicht händisch – deine Änderung wird beim nächsten automatischen Lauf überschrieben. Ändere stattdessen `description`/`description_en` im jeweiligen `plugin.json`.

---

## Branch-Namen

Es gibt (noch) keine streng erzwungene Konvention, aber bitte halte dich an dieses Schema – es macht den PR-Titel selbsterklärend:

| Präfix | Für |
|---|---|
| `plugin/<name>` | Neues Plugin |
| `fix/<kurzbeschreibung>` | Bugfix an einem bestehenden Plugin |
| `docs/<kurzbeschreibung>` | Dokumentation |
| `test/<kurzbeschreibung>` | Änderungen an `tests/` |
| `chore/<kurzbeschreibung>` | Tooling/CI (z.B. automatisch von `update-readme.yml` erzeugte PRs) |

---

## Was bei jedem Pull Request automatisch läuft

Alle Checks müssen grün sein, bevor gemerged werden kann:

| Check | Was er prüft |
|---|---|
| **Plugin Tests** (pytest) | Struktur, Permissions, `verified`-Feld, Dateien, Code-Scanner, Signatur, Syntax – Details in [tests/README.md](tests/README.md) |
| **CodeQL** (Python & JavaScript) | Bekannte Sicherheitslücken-Muster im Code |
| **SonarCloud Quality Gate** | Code Smells, Duplication, neue Issues |

Der CI-Bot kommentiert den PR automatisch mit einer Auswertung nach Testkategorie (📁 Struktur, ✅ Verified, 🔑 Permissions, 📄 Dateien, 🔒 Code-Scanner, 🖊️ Signatur). Bei Fehlern siehe [FAQ.md](FAQ.md#warum-schlägt-mein-pr-fehl).

Dank [CODEOWNERS](.github/CODEOWNERS) wird der Maintainer automatisch als Reviewer auf jeden PR gesetzt.

---

## Review-Kriterien (worauf der Maintainer beim manuellen Review achtet)

- Plugin-Ordner liegt unter `plugins/<name>/` – **nicht im Repo-Root**
- `plugin.json` enthält alle Pflichtfelder und nur Permissions, die das Plugin auch tatsächlich braucht
- Kein Secret/API-Key/Token im Code (Code-Scanner prüft nur gefährliche *Muster*, keine Secrets im Klartext – das ist trotzdem Pflicht)
- DB-Verbindungen sauber in `try`/`finally` geschlossen
- Routen mit Nutzerdaten sind mit `@require_auth()` geschützt
- Bei Multi-Tenant-relevanten Daten: `tenant_id` wird in **jeder** Abfrage berücksichtigt (siehe [docs/PLUGINS.md](docs/PLUGINS.md#-multi-tenant-best-practices))
- Beschreibung in `plugin.json` ist verständlich und nicht irreführend

Plugins, die diese Kriterien erfüllen und alle automatischen Tests bestehen, werden gemerged und erscheinen als "automatisch getestet" im Marketplace. Das **✅ Verifiziert**-Badge kommt erst nach einer zusätzlichen persönlichen Prüfung durch den Maintainer.

---

## Ordner- und Namensregeln

- Plugin-Ordnername: nur `a-z`, `0-9`, `-`, `_`, keine Leerzeichen, lowercase empfohlen
- `plugin_blueprint` in `backend.py` muss exakt so benannt sein
- Eigene DB-Tabellen mit Plugin-Namen präfixen, z.B. `mein_plugin_daten`

---

## Fragen?

Häufige Fragen sind in der [FAQ.md](FAQ.md) gesammelt. Für alles andere: [Issues](https://github.com/Gamerhund/lagersync-plugins/issues).
