# 🤝 Mitmachen

Schön, dass du ein Plugin beisteuern oder an der Doku schrauben willst. So läuft's ab.

## Bevor's losgeht

Schau in [PLUGINS.md](docs/PLUGINS.md) (oder [PLUGINS_KI.md](docs/PLUGINS_KI.md), wenn eine KI das für dich schreibt) und in [EXAMPLES.md](docs/EXAMPLES.md) – vielleicht gibt's dein Use-Case schon als Vorlage. Unsicher ob die Idee überhaupt ins Konzept passt? [Issue](https://github.com/Gamerhund/lagersync-plugins/issues) aufmachen und fragen, lieber vorher als nach drei Stunden Code.

## Ein neues Plugin

1. Forken
2. Branch: `plugin/dein-plugin-name`
3. Ordner unter `plugins/dein-plugin-name/` anlegen – **nicht ins Repo-Root**, das wird nicht geladen (ja, das ist schon jemandem passiert)
4. `plugin.json` mit `"verified": false` und `"enabled": false`. False ist hier die Empfehlung, nicht Pflicht – mehr dazu in [PLUGINS.md](docs/PLUGINS.md#pluginjson--pflichtdatei)
5. Optional: `description_en` in `plugin.json`, falls dein Plugin noch nicht verifiziert ist. Bei bereits signierten Plugins lieber nicht anfassen, dazu unten mehr
6. Lokal testen: `pip install -r requirements.txt && pytest tests/ -v`
7. PR auf `main`, kurz beschreiben was das Plugin macht und wozu die Permissions
8. Checks abwarten, ich schau mir's an
9. Gemerged heißt: automatisch getestet. Das **✅ Verifiziert**-Badge kommt erst, wenn ich mir den Code wirklich persönlich angeschaut habe

## Nur Doku ändern

Gleicher Ablauf, Schritt 3–6 entfällt, Branch-Präfix `docs/`. Eine Sache: Die Plugin-Tabelle in `README.md`/`README_EN.md` wird automatisch generiert (`update-readme.yml`, läuft bei jedem Push auf `main`). Da von Hand reinzuschreiben bringt nichts, das überschreibt der Bot wieder – Beschreibungen ändert man in der jeweiligen `plugin.json`.

## Branch-Namen

Keine harte Regel, aber bitte halbwegs danach:

| Präfix | Wofür |
|---|---|
| `plugin/<name>` | neues Plugin |
| `fix/<kurz>` | Bugfix |
| `docs/<kurz>` | Doku |
| `test/<kurz>` | was an `tests/` |
| `chore/<kurz>` | CI/Tooling |

## Was bei jedem PR automatisch läuft

- **pytest** – Struktur, Permissions, `verified`, Dateien, Code-Scanner, Signatur, Syntax. Details: [tests/README.md](tests/README.md)
- **CodeQL** (Python & JS)
- **SonarCloud Quality Gate**

Alle drei müssen grün sein. Der Bot kommentiert den PR zusätzlich mit einer Aufschlüsselung nach Kategorie – wenn was rot ist, steht meist schon dabei, warum (siehe auch [FAQ.md](FAQ.md#der-pr-ist-rot-was-jetzt)). Über [CODEOWNERS](.github/CODEOWNERS) lande ich automatisch als Reviewer auf jedem PR.

## Worauf ich beim Review schaue

- Ordner liegt wirklich unter `plugins/<name>/`
- Nur Permissions, die das Plugin auch tatsächlich braucht – nicht "könnte ich später mal nutzen"
- Keine Secrets im Code (der Scanner prüft gefährliche Muster, keine Klartext-Keys – Pflicht ist's trotzdem)
- DB-Connections ordentlich in `try`/`finally` zu
- Routen mit Nutzerdaten haben `@require_auth()`
- Bei Multi-Tenant-relevanten Daten: `tenant_id` wird in jeder einzelnen Query mitgeprüft, nicht nur beim Lesen (siehe [PLUGINS.md](docs/PLUGINS.md#-multi-tenant-best-practices))

## Namensregeln

- Plugin-Ordner: `a-z`, `0-9`, `-`, `_`, keine Leerzeichen
- `plugin_blueprint` in `backend.py` muss exakt so heißen
- Eigene DB-Tabellen mit Plugin-Namen prefixen, z.B. `mein_plugin_daten`

Fragen, die wahrscheinlich schon jemand hatte: [FAQ.md](FAQ.md).
