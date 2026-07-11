# 🧩 LagerSync Plugin Marketplace

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=Gamerhund_lagersync-plugins&metric=alert_status)](https://sonarcloud.io/summary/new_code?id=Gamerhund_lagersync-plugins)
[![Plugins](https://img.shields.io/badge/Plugins-5%20verfügbar-blue.svg)](plugins/)

Offizieller Plugin-Marktplatz für [LagerSync](https://lagersync.de). Erweitere deine Lagerverwaltung mit verifizierten Plugins und Community-Erweiterungen – direkt über das Dashboard installierbar. | [English Version](README_EN.md)

---

## 📦 Verfügbare Plugins

| Plugin | Beschreibung | Typ |
|--------|-------------|-----|
| [**ki-assistent**](plugins/ki-assistent/) | KI-Chat mit Ollama/OpenAI. Tool Calling: KI fragt Lagerdaten aktiv ab (search, low stock, locations, stats, change_stock). Skaliert auf beliebig viele Artikel. | ✅ Verifiziert |
| [**low_stock_notifications**](plugins/low_stock_notifications/) | Benachrichtigungen per Telegram, Discord, Webhook oder E-Mail. | ✅ Verifiziert |
| [**price_updater**](plugins/price_updater/) | Aktualisiert EK-Preise automatisch basierend auf konfigurierten URLs. Unterstützt Web Scraping für verschiedene Händler. | 👤 Community |
| [**pro-design**](plugins/pro-design/) | Professionelle Design-Optionen und Themes für deine Lagerverwaltung. | ✅ Verifiziert |
| [**sso**](plugins/sso/) | Single Sign-On per OpenID Connect mit konfigurierbarem Username-Claim, Nonce, Logout, Scope und verbesserter Sicherheit. Funktioniert mit jedem OIDC-Provider. | ✅ Verifiziert |

---

## 🚀 Installation

1. Öffne dein LagerSync-Dashboard
2. Klicke oben in der Navigation auf **🧩 Marketplace**
3. Suche dir ein Plugin aus und klicke auf **„⬇ Installieren"**
4. Nach erfolgreicher Installation: Einstellungen → Plugins → Plugin aktivieren → „Plugins neu laden" → Seite neu laden (Strg+R)

---

## 🛠️ Eigene Plugins entwickeln

Jeder kann Plugins erstellen – du brauchst nur grundlegende Python- oder JavaScript-Kenntnisse.

**Kurzübersicht – Struktur eines Plugins:**

```
plugins/
└── mein-plugin/
    ├── plugin.json     ← Pflichtdatei (Name, Permissions, ...)
    ├── plugin.sig      ← Nur für verifizierte Plugins 
    ├── backend.py      ← Optional: Flask-API-Routen
    └── frontend.js     ← Optional: Browser-UI
```

| Dokumentation | Für wen |
|---|---|
| [PLUGINS.md](docs/PLUGINS.md) | Entwickler – vollständige, menschenlesbare Dokumentation |
| [PLUGINS_KI.md](docs/PLUGINS_KI.md) | KI-gestützte Entwicklung – speziell für KI-Agenten aufbereitet |
| [EXAMPLES.md](docs/EXAMPLES.md) | Vier vollständige Beispiel-Plugins zum Abschauen |
| [ARCHITECTURE.md](docs/ARCHITECTURE.md) | Wie ein Plugin technisch ins System eingebunden wird |
| [SECURITY.md](docs/SECURITY.md) | Sicherheitsmodell & Schwachstellen melden |
| [FAQ.md](FAQ.md) | Häufige Fragen & Troubleshooting |
| [CONTRIBUTING.md](CONTRIBUTING.md) | Ablauf für Pull Requests |

**Tipp für KI-gestützte Entwicklung:** Gib [docs/PLUGINS_KI.md](docs/PLUGINS_KI.md) einer KI (z.B. Claude oder ChatGPT) und beschreibe was dein Plugin tun soll – sie generiert direkt PR-fertigen Code der alle automatischen Tests besteht.

---

## 📤 Plugin veröffentlichen

Der vollständige Ablauf inkl. Branch-Namen, Pflicht-Checks und Review-Kriterien steht in [CONTRIBUTING.md](CONTRIBUTING.md). Kurzfassung:

1. [Fork dieses Repository](https://github.com/Gamerhund/lagersync-plugins/fork)
2. Erstelle einen neuen Ordner unter `plugins/` für dein Plugin
3. Füge deine Dateien hinzu: `plugin.json`, optional `backend.py` und `frontend.js`
   - `plugin.json` muss die Pflichtfelder `name`, `version`, `author`, `description`, `verified`, `enabled` und `permissions` enthalten.
   - Für neue Plugins: `verified: false`; `enabled: false` ist empfohlen.
4. Erstelle einen **Pull Request** mit kurzer Beschreibung
5. Nach Review und Tests erscheint dein Plugin im Marketplace

---

## 🤝 Beitragen

Contributions sind willkommen! Bitte lies [CONTRIBUTING.md](CONTRIBUTING.md) bevor du anfängst – dort stehen Branch-Namen, Testpflichten und Review-Kriterien. Für Bugs und Feature-Wünsche nutze die [Issues](https://github.com/Gamerhund/lagersync-plugins/issues), für wiederkehrende Fragen gibt's die [FAQ.md](FAQ.md).

---

## 📄 Lizenz

[MIT](LICENSE) © 2026 Jonas (Gamerhund)

---

## ☕ Projekt unterstützen

Wenn dir dieses Plugin-System oder LagerSync nützlich ist, würde ich mich über deine Unterstützung freuen – sie hilft mir, neue Features zu entwickeln, Bugs zu beheben und das Projekt langfristig zu pflegen.

- ☕ Ko-fi: [https://ko-fi.com/gamerhund](https://ko-fi.com/gamerhund)
- ₿ Bitcoin: `bc1qha4h4vvykgcvzdgc5auueqhq0lf4glstrs0cy`

Danke für deine Unterstützung! 💚