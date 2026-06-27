# ❓ FAQ

Häufige Fragen rund um Plugin-Entwicklung, Pull Requests und den Marketplace. Tiefere Details stehen jeweils in [docs/PLUGINS.md](docs/PLUGINS.md).

---

## Warum erscheint mein Plugin nicht im Marketplace?

Prüfe in dieser Reihenfolge:

1. Ist der PR gemerged? Vor dem Merge ist das Plugin nur im PR sichtbar, nicht im Marketplace.
2. Liegt dein Plugin-Ordner wirklich unter `plugins/<name>/`? Ein `plugin.json` direkt im Repo-Root wird **nicht** geladen (das ist genau das, was bei [Test Plugin V5](https://github.com/Gamerhund/lagersync-plugins/pull/10) versehentlich passiert ist).
3. Ist `plugin.json` gültiges JSON und enthält alle Pflichtfelder (`name`, `version`, `author`, `description`, `verified`, `enabled`)?
4. Steht `"enabled": false`? Dann wird das Plugin beim Start nicht geladen.

## Warum schlägt mein PR fehl?

Der CI-Bot kommentiert deinen PR mit einer Auswertung nach Kategorie. Schau zuerst dort nach, welche Kategorie fehlschlägt:

| Kategorie im Bot-Kommentar | Mögliche Ursache |
|---|---|
| 📁 Struktur | `plugin.json` fehlt/ungültig, Pflichtfeld fehlt, Version nicht im Format `X.Y.Z`, Ordnername mit Großbuchstaben/Leerzeichen |
| ✅ Verified | `"verified": true` in einem neuen Plugin gesetzt – das darfst du nicht selbst, siehe [unten](#warum-darf-ich-verified-nicht-selbst-auf-true-setzen) |
| 🔑 Permissions | Eine Permission in `plugin.json`, die nicht in der [gültigen Liste](docs/PLUGINS.md#plugin-sicherheit) steht, oder `permissions` ist kein Array |
| 📄 Dateien | `backend.py` hat einen Syntaxfehler oder definiert kein `plugin_blueprint`; `frontend.js` ist leer |
| 🔒 Code-Scanner | Ein gefährliches Muster wie `eval()`, `subprocess`, `os.system()` o.ä. im Code – siehe [SECURITY.md](docs/SECURITY.md#2-code-scanner-statische-analyse-beim-laden) |
| 🖊️ Signatur | Nur relevant bei `"verified": true` ohne gültige `plugin.sig` – als neues Plugin sollte das nicht auftreten |

Zusätzlich müssen **CodeQL** und der **SonarCloud Quality Gate** grün sein – beide laufen unabhängig von den pytest-Checks. Schau in die jeweiligen Check-Details im PR für die genaue Fehlermeldung.

## Warum darf ich `verified` nicht selbst auf `true` setzen?

`verified: true` bedeutet "der Maintainer hat den Code persönlich geprüft und freigegeben" – nicht "die automatischen Tests sind grün". Ein neues Plugin mit `"verified": true` schlägt deshalb absichtlich den Test `test_plugin_verified.py` fehl. Lass das Feld auf `false`; der Maintainer setzt es nach Prüfung zusammen mit der Ed25519-Signatur.

## Warum funktioniert mein `frontend.js` nicht?

- Öffne die Browser-Konsole (DevTools) – Syntaxfehler oder Laufzeitfehler werden dort angezeigt, das Script läuft aber lokal nicht im CI-Browser, nur `node --check` prüft die Syntax.
- `frontend.js` darf nicht leer sein (`test_plugin_files.py` prüft das).
- `pluginId` und `PluginAPI` sind nur zur Laufzeit im Browser verfügbar, nicht in einem reinen Node-Kontext – ein lokaler `node frontend.js`-Test schlägt deshalb mit `PluginAPI is not defined` fehl, das ist normal.

## Welche Permissions darf ich nutzen?

Die vollständige, gültige Liste steht in [docs/PLUGINS.md](docs/PLUGINS.md#plugin-sicherheit) und wird von `test_plugin_permissions.py` gegen genau diese Liste geprüft. Fordere nur an, was du wirklich brauchst – das beschleunigt auch die manuelle Review (siehe [CONTRIBUTING.md](CONTRIBUTING.md#review-kriterien)).

## Wie teste ich mein Plugin lokal, bevor ich den PR erstelle?

```bash
pip install -r requirements.txt
pytest tests/ -v
```

Einzelne Kategorie:
```bash
pytest tests/test_plugin_structure.py -v
```

Der JavaScript-Syntax-Check (`test_plugin_syntax.py::test_javascript_syntax`) braucht lokal installiertes Node.js (`node --check`) – ist Node nicht installiert, wird der Test übersprungen statt zu scheitern, lokal wie in CI.

## Was ist der Unterschied zwischen `PLUGINS.md` und `PLUGINS_KI.md`?

`docs/PLUGINS.md` ist die vollständige, menschenlesbare Referenz. `docs/PLUGINS_KI.md` ist eine verdichtete Regel-Checkliste für KI-Agenten, die direkt Code generieren sollen. Bei Widersprüchen zwischen beiden gilt `PLUGINS.md` – siehe den Hinweis am Anfang von `PLUGINS_KI.md`.

## Warum steht in der englischen README plötzlich Deutsch / warum hat sich die Plugin-Tabelle in der README verändert, obwohl ich sie nicht angefasst habe?

Die Plugin-Tabelle und der "X verfügbar"-Badge werden automatisch von `.github/scripts/update_readme.py` aus `plugins/*/plugin.json` erzeugt, sobald jemand nach `main` pusht (als eigener PR von `github-actions[bot]`, kein Direkt-Commit). Bearbeite die Tabelle deshalb nicht händisch in der README.

Für die englische Beschreibung gilt: Neue, noch unsignierte Plugins können einfach `description_en` in ihrer `plugin.json` ergänzen. Bei bereits **verifizierten** Plugins würde das die Ed25519-Signatur (`plugin.sig`) invalidieren, deshalb pflegt der Maintainer deren englische Texte direkt in einer kleinen Übersetzungstabelle (`VERIFIED_PLUGIN_DESCRIPTIONS_EN`) im Skript selbst.

## Ich will Netzwerkzugriff (z.B. einen Webhook aufrufen) – wie?

Nicht über `socket` oder ähnliche Low-Level-Module (die blockiert der Code-Scanner). Fordere stattdessen die Permission `system.network` an und nutze `PluginAPI.fetch()` im Frontend, oder rufe externe APIs aus `backend.py` mit `requests`/`urllib` auf, sofern das in deinem Kontext erlaubt ist – schau dir `low_stock_notifications` als Referenz für Webhook/Telegram/Discord-Versand an.

## Kann ich ein bereits veröffentlichtes Plugin updaten?

Ja – neuer PR, der `plugin.json` (Version erhöhen, am besten nach [SemVer](docs/PLUGINS.md#-versionierung--migration)) und die Code-Dateien im bestehenden Plugin-Ordner ändert. Bei strukturellen Datenbank-Änderungen siehe die Migrations-Hinweise in `docs/PLUGINS.md`.

## Mein Plugin braucht eine Bibliothek, die nicht in `requirements.txt` steht – geht das?

`requirements.txt` in diesem Repo ist nur für die **Test-Infrastruktur** (pytest, cryptography). Was dein Plugin zur Laufzeit importieren darf, hängt von dem ab, was die LagerSync-Hauptanwendung bereitstellt, nicht von diesem Repo. Frag im entsprechenden Issue/PR nach, falls unklar.

---

Frage nicht beantwortet? Öffne ein [Issue](https://github.com/Gamerhund/lagersync-plugins/issues).
