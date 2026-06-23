# 🧩 LagerSync Plugin Marketplace

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=Gamerhund_lagersync-plugins&metric=alert_status)](https://sonarcloud.io/summary/new_code?id=Gamerhund_lagersync-plugins)
[![Plugins](https://img.shields.io/badge/Plugins-3%20verfügbar-blue.svg)](plugins/)
| [English Version](README_EN.md)
Offizieller Plugin-Marktplatz für [LagerSync](https://lagersync.de). Erweitere deine Lagerverwaltung mit verifizierten Plugins und Community-Erweiterungen – direkt über das Dashboard installierbar.

---

## 📦 Verfügbare Plugins

| Plugin | Beschreibung | Typ |
|--------|-------------|-----|
| [**ki-assistent**](plugins/ki-assistent/) | KI-Chat mit Ollama & OpenAI-Integration. Kann Lagerbestände abfragen und Bestandsänderungen vornehmen. | ✅ Verifiziert |
| [**low_stock_notifications**](plugins/low_stock_notifications/) | Benachrichtigungen per Telegram, Discord, Webhook oder E-Mail bei Unterschreitung des Mindestbestands. | ✅ Verifiziert |
| [**pro-design**](plugins/pro-design/) | Professionelle Design-Optionen und Themes für deine Lagerverwaltung. | ✅ Verifiziert |

---

## 🚀 Installation

1. Öffne dein LagerSync-Dashboard
2. Gehe zu **Einstellungen → 🧩 Plugins**
3. Klicke auf „Plugin installieren"
4. Wähle das Plugin aus der Liste
5. Klicke auf „Installieren"

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
| [PLUGINS.md](PLUGINS.md) | Entwickler – vollständige, menschenlesbare Dokumentation |
| [PLUGINS_KI.md](PLUGINS_KI.md) | Vibe Coding – speziell für KI-Agenten aufbereitet |

**Tipp für Vibe Coding:** Gib [PLUGINS_KI.md](PLUGINS_KI.md) einer KI (z.B. Claude oder ChatGPT) und beschreibe was dein Plugin tun soll – sie generiert direkt PR-fertigen Code der alle automatischen Tests besteht.

---

## 📤 Plugin veröffentlichen

1. [Fork dieses Repository](https://github.com/Gamerhund/lagersync-plugins/fork)
2. Erstelle einen neuen Ordner unter `plugins/` für dein Plugin
3. Füge deine Dateien hinzu: `plugin.json`, optional `backend.py` und `frontend.js`
4. Erstelle einen **Pull Request** mit kurzer Beschreibung
5. Nach Review und Tests erscheint dein Plugin im Marketplace

---

## 🤝 Beitragen

Contributions sind willkommen! Bitte lies [PLUGINS.md](PLUGINS.md) bevor du anfängst. Für Bugs und Feature-Wünsche nutze die [Issues](https://github.com/Gamerhund/lagersync-plugins/issues).

---

## 📄 Lizenz

[MIT](LICENSE) © 2026 Jonas (Gamerhund)
