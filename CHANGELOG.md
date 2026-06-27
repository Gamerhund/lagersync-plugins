# 📦 Changelog

Alle nennenswerten Änderungen am **Marketplace-Repository** (nicht an einzelnen Plugins – die haben ihre eigene Version in `plugin.json`). Format angelehnt an [Keep a Changelog](https://keepachangelog.com/), aber datumsbasiert statt versioniert, da dieses Repo selbst kein eigenständig veröffentlichtes Paket ist.

## [Unreleased]

### Added
- Repository-Dokumentation neu strukturiert: `docs/`-Ordner für `PLUGINS.md`, `PLUGINS_KI.md`, sowie neue `ARCHITECTURE.md`, `EXAMPLES.md`, `SECURITY.md`
- `CONTRIBUTING.md`, `CHANGELOG.md`, `FAQ.md` im Repo-Root
- `update_readme.py`: optionales `description_en`-Feld in `plugin.json` für neue, unsignierte Plugins

### Changed
- Sicherheitsmechanismen (Signaturen, Audit-Logs, Rate Limiting, Code-Scanner) aus `PLUGINS.md` nach `docs/SECURITY.md` ausgelagert
- `tests/README.md` und `PLUGINS_KI.md` korrigiert: zwei bisher undokumentierte Test-Dateien (`test_plugin_code_scan.py`, `test_plugin_syntax.py`) ergänzt

### Fixed
- **Englische README zeigte deutsche Plugin-Beschreibungen.** `update_readme.py` nutzte für beide Sprachen dasselbe `description`-Feld. Behoben durch eine Übersetzungstabelle für die vier bereits signierten Plugins (`VERIFIED_PLUGIN_DESCRIPTIONS_EN`) plus optionalem `description_en`-Feld für künftige, noch unsignierte Plugins – ohne die bestehenden Ed25519-Signaturen anzufassen
- Entfernt: ein `plugin.json` ("Test Plugin V5"), das versehentlich im Repo-Root statt unter `plugins/` gelandet war (Überbleibsel aus PR #10) und dort nie geladen wurde

---

## 2026-06-26 — Automatisches README-Update, CODEOWNERS, Plugin-Test-Mishap

### Added
- `update_readme.py` + Workflow `update-readme.yml`: generiert die Plugin-Tabelle und den "X verfügbar"-Badge in README.md/README_EN.md automatisch aus `plugins/*/plugin.json` bei jedem Push nach `main` (#9)
- `.github/CODEOWNERS`: Maintainer wird automatisch als Reviewer auf jeden PR gesetzt (#12)
- `workflow_dispatch` Trigger für `test.yml`, erlaubt manuelles Auslösen der Tests (#11)

### Fixed
- Mehrere Iterationen am PR-Workflow des README-Updaters (#13, #14, #15) – der Bot committet jetzt über einen eigenen Branch + PR statt direkt nach `main`
- Plugin-Anzahl in README.md/README_EN.md mehrfach nachgezogen, bis der Auto-Updater stand (#7, #8, #17, #20)

### Removed
- `plugins/test-plugin-v5/` wieder entfernt – Test-Plugin aus einem Workflow-Test-PR (#10, gelöscht in #18)

---

## 2026-06-26 — Erweiterte Plugin-Dokumentation

### Added
- Abschnitte zu Performance-Optimierung, Debugging, Testing, Error Handling, Multi-Tenant Best Practices, Versionierung/Migration, Troubleshooting und Development Workflow in `PLUGINS.md` und `PLUGINS_KI.md` (#6)

### Changed
- Begriff "Vibe Coding" durchgängig durch "KI-gestützte Entwicklung" ersetzt (README, README_EN, PLUGINS_KI.md)

---

## 2026-06-24 — Security-Fixes & SSO-Refactor

### Security
- SSRF- und XSS-Schwachstellen in Plugins behoben (#5)

### Changed
- SSO-Frontend überarbeitet, Tests ergänzt, Benachrichtigungs-Logik refactored

---

## 2026-06-20 – 2026-06-23 — SSO-Plugin, englische Doku, Code-Qualität

### Added
- Neues Plugin: **sso** – Single Sign-On per OpenID Connect (Authentik, Keycloak, Entra ID, ...)
- `README_EN.md` (englische Version der README)
- SonarCloud Quality-Gate-Badge in der README

### Changed
- `sso`: konfigurierbarer Username-Claim, Scope, Nonce und Logout ergänzt
- SonarQube Code Smells in mehreren Plugins behoben (u.a. KI-Chat-Refactor, doppelte Utility-Funktionen entfernt, async IIFE durch top-level await ersetzt)

---

## 2026-05-29 – 2026-05-30 — CI-Automatisierung

### Added
- Neue Tests: Code-Scanner, Dateinamen-Konventionen, Blueprint-Validierung
- Automatischer PR-Kommentar-Bot (`pr_review_analyzer.py`) mit Testergebnis-Zusammenfassung nach Kategorie

### Fixed
- `requirements.txt` für pip-Cache in GitHub Actions ergänzt

---

## 2026-05-25 — Initial Release

### Added
- Marketplace-Repository mit drei initialen Plugins: **ki-assistent** (KI-Chat mit Ollama/OpenAI), **low_stock_notifications** (Telegram/Discord/Webhook/E-Mail bei Mindestbestand), **pro-design** (Themes)
- Erste Version von `PLUGINS.md` und Plugin-Tests
