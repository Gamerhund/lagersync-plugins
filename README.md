# LagerSync Plugin Marketplace

Offizieller Plugin-Marktplatz für LagerSync. Hier findest du verifizierte Plugins und Community-Erweiterungen für deine Lagerverwaltung.

## Struktur eines Plugins

```
lagersync-plugins/
  plugins/
    mein-plugin/
      plugin.json      ← Pflichtdatei
      backend.py       ← optional
      frontend.js      ← optional
```

## Verfügbare Plugins

- **ki-assistent** – KI-Chat mit Ollama/OpenAI-Integration
- **low_stock_notifications** – Benachrichtigungen per Telegram, Discord, Webhook oder E-Mail
- **pro-design** – Alternatives cleanes Web-Design

## Installation

### Über das Dashboard (empfohlen)
1. Öffne dein LagerSync-Dashboard
2. Gehe zu Einstellungen → 🧩 Plugins
3. Klicke auf „Plugin installieren"
4. Wähle das Plugin aus der Liste
5. Klicke auf „Installieren"

### Manuell von GitHub
1. Lade das Plugin als ZIP herunter (`Code → Download ZIP`)
2. Entpacke es in deinen `/plugins/` Ordner
3. Gehe zu Einstellungen → 🧩 Plugins → **Neu laden**
4. Aktiviere das Plugin

## Eigene Plugins veröffentlichen

1. Fork dieses Repositories: https://github.com/Gamerhund/lagersync-plugins
2. Erstelle einen neuen Ordner unter `plugins/` für dein Plugin
3. Füge deine Dateien hinzu: `plugin.json`, `backend.py`, `frontend.js`
4. Erstelle einen Pull Request
5. Nach Review und Merge wird dein Plugin im Marketplace angezeigt

Siehe [PLUGINS.md](PLUGINS.md) für die vollständige Plugin-Entwicklungsdokumentation.
