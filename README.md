# 🧩 LagerSync Plugin Marketplace

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Plugins](https://img.shields.io/badge/Plugins-3%20verfügbar-blue.svg)](plugins/)

Offizieller Plugin-Marktplatz für [LagerSync](https://github.com/Gamerhund). Erweitere deine Lagerverwaltung mit verifizierten Plugins und Community-Erweiterungen – direkt über das Dashboard installierbar.

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

Jeder kann Plugins erstellen – du brauchst nur grundlegende Python- oder JavaScript-Kenntnisse. Die vollständige Dokumentation findest du in [PLUGINS.md](PLUGINS.md).

**Kurzübersicht – Struktur eines Plugins:**

```
plugins/
└── mein-plugin/
    ├── plugin.json     ← Pflichtdatei (Name, Permissions, ...)
    ├── backend.py      ← optional: eigene Flask-API-Routen
    └── frontend.js     ← optional: Browser-UI
```

**KI-Unterstützung:** Gib [PLUGINS.md](PLUGINS.md) einfach einer KI (z.B. Claude oder ChatGPT) und beschreibe was dein Plugin tun soll – die Dokumentation enthält alle nötigen Infos für automatische Plugin-Generierung.

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
