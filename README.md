# Plugin Marketplace (lokal / offline)

Lege neue Plugins als Unterordner hier ab. Jeder Ordner braucht eine `plugin.json`.

## Struktur eines Plugins

```
marketplace/
  mein-plugin/
    plugin.json      ← Pflichtdatei
    backend.py       ← optional
    frontend.js      ← optional
```

## plugin.json Beispiel

```json
{
  "id": "mein-plugin",
  "name": "Mein Plugin",
  "description": "Was das Plugin macht",
  "version": "1.0.0",
  "author": "Gamerhund",
  "category": "inventory",
  "tags": ["tool", "export"],
  "enabled": false
}
```

## Installation

Im Einstellungsmenü unter **Plugins → Marketplace** auf „Installieren" klicken.
Das Plugin wird dann nach `/plugins/` kopiert und ist aktivierbar.

Keine Internetverbindung erforderlich.
