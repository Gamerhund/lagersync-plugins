# 🧩 Plugin-Entwicklung – LagerSync

Diese Dokumentation richtet sich an Entwickler, die Plugins für die Lagerverwaltung erstellen wollen.

---

## Schnellstart

Ein Plugin ist ein **Ordner** im `plugins/` Verzeichnis dieses Repositories:

```
lagersync-plugins/
└── plugins/
    └── mein-plugin/
        ├── plugin.json     ← Pflicht
        ├── plugin.sig      ← Optional: Ed25519 Signatur
        ├── backend.py      ← Optional: eigene API-Routen (Flask)
        └── frontend.js     ← Optional: Browser-Code
```

---

## plugin.json – Pflichtdatei

```json
{
  "name": "Mein Plugin",
  "version": "1.0.0",
  "author": "Dein Name oder GitHub-Username",
  "description": "Kurze Beschreibung was das Plugin macht.",
  "verified": false,
  "enabled": true,
  "permissions": [
    "inventory.read",
    "inventory.write",
    "notifications.send"
  ]
}
```

| Feld | Typ | Pflicht | Beschreibung |
|------|-----|---------|-------------|
| `name` | string | ✅ | Anzeigename im Plugin-Manager |
| `version` | string | – | Versionsnummer, z.B. `"1.2.0"` |
| `author` | string | – | Name des Entwicklers |
| `description` | string | – | Kurzbeschreibung |
| `verified` | bool | – | Wird **ausschließlich vom Maintainer** gesetzt – niemals selbst auf `true` setzen. `false` = Plugin hat automatische Tests bestanden und ist verfügbar. `true` = Persönlich vom Maintainer geprüft (✅ Badge). |
| `enabled` | bool | – | `false` = Plugin wird beim Start nicht geladen |
| `permissions` | array | – | Liste der benötigten Berechtigungen (siehe unten) |

---

## Datenbank-Schema

Das System verwendet **SQLite**. Folgende Tabellen stehen Plugins zur Verfügung:

### `products` *(Permission: `inventory.read` / `inventory.write`)*

| Spalte | Typ | Beschreibung |
|--------|-----|--------------|
| `id` | INTEGER | Primärschlüssel |
| `name` | TEXT | Produktname |
| `barcode` | TEXT | EAN/QR-Code (eindeutig) |
| `short` | TEXT | Kurzkürzel |
| `min_stock` | INTEGER | Mindestbestand |

### `inventory` *(Permission: `inventory.read` / `inventory.write`)*

| Spalte | Typ | Beschreibung |
|--------|-----|--------------|
| `product_id` | INTEGER | FK → `products.id` |
| `location_id` | INTEGER | FK → `locations.id` |
| `quantity` | INTEGER | Aktuelle Menge |

### `locations` *(Permission: `inventory.read`)*

| Spalte | Typ | Beschreibung |
|--------|-----|--------------|
| `id` | INTEGER | Primärschlüssel |
| `name` | TEXT | Name des Lagerorts |

### `users` *(Permission: `users.read` / `users.write`)*

| Spalte | Typ | Beschreibung |
|--------|-----|--------------|
| `username` | TEXT | Benutzername (eindeutig) |
| `is_admin` | INTEGER | `1` = Admin, `0` = normaler Nutzer |

### `settings` *(Permission: `system.settings`)*

| Spalte | Typ | Beschreibung |
|--------|-----|--------------|
| `key` | TEXT | Einstellungsschlüssel (eindeutig) |
| `value` | TEXT | Wert als JSON-String oder Plaintext |

> 💡 Plugin-eigene Tabellen mit Plugin-Name als Präfix benennen, z.B. `mein_plugin_daten`.

---

## 🔒 Plugin-Sicherheit

### Permissions System

Plugins müssen **explizit** Berechtigungen anfordern. Ohne Permission werden API-Aufrufe blockiert.

**Verfügbare Permissions:**

| Permission | Beschreibung |
|------------|--------------|
| `db.read` | Datenbank lesen |
| `db.write` | Datenbank schreiben |
| `inventory.read` | Produkte und Bestände lesen |
| `inventory.write` | Produkte und Bestände ändern |
| `inventory.delete` | Produkte löschen |
| `users.read` | Benutzerdaten lesen |
| `users.write` | Benutzer erstellen/bearbeiten |
| `system.settings` | Einstellungen ändern |
| `system.files.read` | Dateisystem lesen (eingeschränkt) |
| `system.files.write` | Dateisystem schreiben (eingeschränkt) |
| `system.network` | Netzwerkzugriff |
| `notifications.send` | Benachrichtigungen senden |
| `api.public` | Öffentliche API nutzen |
| `api.admin` | Admin-API nutzen |

**Default-Permissions für neue Plugins:**
```json
["db.read", "inventory.read", "api.public"]
```

### Plugin-Signaturen (Ed25519)

Offizielle Plugins können kryptografisch signiert werden.

**Signatur erstellen (für Entwickler):**
```bash
# Private Key generieren (einmalig)
python -c "from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey; \
import base64; key = Ed25519PrivateKey.generate(); \
print('Private:', base64.b64encode(key.private_bytes_raw()).decode()); \
print('Public:', base64.b64encode(key.public_key().public_bytes_raw()).decode())"
```

**plugin.sig Datei:**
```
base64-encoded-signature
```

### Audit-Logs

Alle Plugin-Aktionen werden protokolliert:
- Plugin geladen/entladen
- API-Aufrufe
- Datenbank-Zugriffe
- Konfigurationsänderungen

```
GET /api/plugins/{plugin_id}/audit
```

### Rate Limiting

| Aktion | Limit |
|--------|-------|
| Default | 100 / 60s |
| db.read | 50 / 60s |
| db.write | 20 / 60s |
| api.public | 100 / 60s |
| api.admin | 30 / 60s |

```
GET /api/plugins/{plugin_id}/rate-limits
```

### Code-Scanner

Beim Laden werden Plugins auf gefährliche Muster gescannt:

- `os.system()` – Befehlsausführung
- `subprocess` – Prozessausführung
- `eval()` / `exec()` – Code-Ausführung
- `socket` – Netzwerkzugriff
- `shutil.rmtree` – Verzeichnis löschen
- `pickle` – Unsichere Deserialisierung

```
GET /api/plugins/{plugin_id}/scan
```

---

## backend.py – Eigene API-Routen

```python
from flask import Blueprint

# Pflicht: muss "plugin_blueprint" heißen
plugin_blueprint = Blueprint('mein_plugin', __name__)

@plugin_blueprint.route('/hallo', methods=['GET'])
def hallo():
    return json_response({'nachricht': 'Hallo!'})
```

### Injizierte Variablen

Diese Variablen stehen **ohne Import** zur Verfügung – der Plugin-Loader injiziert sie automatisch:

| Variable | Typ | Beschreibung |
|---|---|---|
| `get_db_connection()` | Funktion | Gibt eine SQLite-Verbindung zurück |
| `require_auth()` | Decorator | Schützt Routen (Login erforderlich) |
| `json_response(obj, status)` | Funktion | Gibt JSON-Antwort zurück (orjson-optimiert) |
| `user_is_admin(name)` | Funktion | Prüft ob ein Benutzer Admin ist |
| `get_setting_value(key)` | Funktion | Liest einen Wert aus der Settings-Tabelle |
| `app` | Flask App | Die Flask-App-Instanz |
| `session` | Flask session | Aktuelles Session-Objekt |
| `request` | Flask request | Aktuelles Request-Objekt |
| `jsonify` | Funktion | Flask jsonify |
| `ADMIN_TOKEN` | string | Der konfigurierte Admin-Token |
| `os` | Modul | Python os-Modul |
| `json` | Modul | Python json-Modul |

### Routen-URLs

Alle Backend-Routen sind automatisch unter diesem Präfix erreichbar:

```
/api/plugin/{plugin-ordner-name}/deine-route
```

Beispiel: Plugin-Ordner `pos-system`, Route `/status` → `/api/plugin/pos-system/status`

### Datenbank nutzen

```python
@plugin_blueprint.route('/meine-daten', methods=['GET'])
def meine_daten():
    conn = get_db_connection()
    c = conn.cursor()
    try:
        c.execute('SELECT COUNT(*) as n FROM products')
        row = c.fetchone()
        return json_response({'anzahl': row['n']})
    finally:
        conn.close()
```

### Eigene DB-Tabellen anlegen

```python
def _init_plugin_tables():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS mein_plugin_daten (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        key TEXT UNIQUE,
        value TEXT,
        created INTEGER
    )''')
    conn.commit()
    conn.close()

# Beim Blueprint-Start aufrufen
try:
    _init_plugin_tables()
except Exception as e:
    print(f'[mein-plugin] DB-Init Fehler: {e}')
```

### Auth schützen

```python
@plugin_blueprint.route('/admin-bereich', methods=['GET'])
@require_auth()
def admin_bereich():
    return json_response({'geheim': 'Nur für Admins'})
```

---

## frontend.js – Browser-Code

Das Script wird automatisch auf jeder Seite geladen. Es läuft in einem **IIFE** (Immediately Invoked Function Expression) – Variablenname-Konflikte mit anderen Plugins sind ausgeschlossen.

Die Variable `pluginId` enthält die Plugin-ID (Ordnername).

### PluginAPI

```javascript
// Menü-Eintrag unter Einstellungen hinzufügen
PluginAPI.addMenuItem('Mein Plugin', '🔌', function() {
    openMeinPluginModal();
});

// Auf Events der Hauptanwendung reagieren
PluginAPI.onEvent('bestand_geaendert', function(data) {
    console.log('Bestand hat sich geändert:', data);
});

// Eigene Events auslösen (für andere Plugins oder die Hauptanwendung)
PluginAPI.emitEvent('mein_event', { info: 'Hallo' });

// Backend-API aufrufen (automatisch mit korrektem Präfix)
const resp = await PluginAPI.fetch(pluginId, '/meine-route');
const data = await resp.json();
```

### Verfügbare Events

| Event | Wird ausgelöst wenn | Data |
|---|---|---|
| `bestand_geaendert` | Bestandsmenge geändert | `{ productKey, delta }` |
| `produkt_erstellt` | Neues Produkt angelegt | `{ productKey }` |
| `produkt_geloescht` | Produkt gelöscht | `{ productKey }` |
| `standort_gewechselt` | Benutzer wechselt Lagerort-Ansicht | `{ locationId }` |

> **Hinweis:** Events werden über `PluginAPI.emitEvent(...)` ausgelöst. Um die Hauptanwendung anzupassen, müssen die entsprechenden Stellen in `index.html` um `PluginAPI.emitEvent(...)` Aufrufe ergänzt werden.

### Modal erstellen

```javascript
function openMeinPluginModal() {
    const m = document.createElement('div');
    m.className = 'modal';
    m.style.display = 'flex';
    m.innerHTML = `
        <div class="modal-content" style="max-width:500px;width:95vw">
            <h3>🔌 Mein Plugin</h3>
            <p>Plugin-Inhalt hier.</p>
            <button class="btn" onclick="this.closest('.modal').remove()">Schließen</button>
        </div>
    `;
    document.body.appendChild(m);
    m.addEventListener('click', e => { if (e.target === m) m.remove(); });
}
```

### Globale Funktionen der Hauptanwendung nutzen

Vorsicht: Diese können sich mit Updates ändern. Stabile Kandidaten:

```javascript
// Toast-Nachricht anzeigen
showToast && showToast('✅ Erledigt!');

// Produkt-Datenbank lesen (read-only)
const db = window.productDatabase || {};

// Scanner öffnen
openScannerSelectModal && openScannerSelectModal();
```

---

## Vollständiges Beispiel: Dummy-Plugin (Tutorial)

Dies ist ein **Beispiel** für Entwickler – kein echtes Plugin.

**plugin.json:**
```json
{
  "name": "Mein Plugin",
  "version": "1.0.0",
  "author": "DeinName",
  "description": "Ein Beispiel-Plugin zum Testen.",
  "verified": false,
  "enabled": true
}
```

**backend.py:**
```python
from flask import Blueprint
plugin_blueprint = Blueprint('mein_plugin', __name__)

@plugin_blueprint.route('/hallo', methods=['GET'])
@require_auth()
def hallo():
    """Gibt eine Test-Antwort zurück."""
    return json_response({'status': 'ok', 'nachricht': 'Hallo!'})
```

**frontend.js:**
```javascript
PluginAPI.addMenuItem('Mein Plugin', '🔌', async function() {
    try {
        const resp = await PluginAPI.fetch(pluginId, '/hallo');
        const data = await resp.json();
        alert('Antwort: ' + data.nachricht);
    } catch(e) {
        alert('Fehler: ' + e.message);
    }
});
```

---

## Plugin veröffentlichen (lagersync-plugins Repo)

1. Fork dieses Repositories: https://github.com/Gamerhund/lagersync-plugins
2. Erstelle einen neuen Ordner unter `plugins/` für dein Plugin
3. Füge deine Dateien hinzu: `plugin.json`, `backend.py`, `frontend.js`
4. Setze `"verified": false` in `plugin.json` – wird vom Maintainer gesetzt, nicht selbst
5. Erstelle einen Pull Request
6. Automatische Tests laufen durch – bei Erfolg wird das Plugin in den Marketplace aufgenommen
7. Nach persönlicher Prüfung durch den Maintainer erhält das Plugin das **✅ Verifiziert**-Badge

**Nutzer können dann:**
- Plugin direkt über das Dashboard installieren (GitHub-Download)

---

## Plugin-Ordner Namensregeln

- Nur Buchstaben, Zahlen, Bindestrich und Unterstrich: `a-z A-Z 0-9 - _`
- Keine Leerzeichen oder Sonderzeichen
- Lowercase empfohlen: `ki-assistent`, `low_stock_notifications`, `mein-plugin`

---

## Sicherheitshinweis

> 🔒 **Security-Level: 8-9/10** – Das Plugin-System verfügt über:
> - **Permissions System** – Plugins müssen Berechtigungen explizit anfordern
> - **Ed25519 Signaturen** – Offizielle Plugins sind kryptografisch signiert
> - **Audit-Logs** – Alle Aktionen werden protokolliert
> - **Rate Limiting** – API-Aufrufe sind pro Zeiteinheit begrenzt
> - **Code-Scanner** – Beim Laden wird auf gefährliche Muster geprüft

Plugins ohne Verified-Badge wurden automatisch getestet, aber noch nicht persönlich geprüft. Getestete und verifizierte Plugins tragen das **✅ Verifiziert** Badge (`"verified": true`, gesetzt vom Maintainer).

> ⚠️ **Trotz Sicherheitsmaßnahmen:** Installiere nur Plugins deren Quellcode du gelesen und verstanden hast. Externe Plugins können potenziell schädlichen Code enthalten, der nicht vom Scanner erkannt wird.

---

*Lizenz: MIT © 2026 Jonas (Gamerhund)*
