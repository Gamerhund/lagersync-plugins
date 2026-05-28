# 🧩 Plugin-Entwicklung – LagerSync

Diese Dokumentation richtet sich an **Entwickler und KI**, die Plugins für die Lagerverwaltung erstellen wollen.

---

## Inhaltsverzeichnis

1. [Schnellstart](#schnellstart)
2. [plugin.json – Pflichtdatei](#pluginjson--pflichtdatei)
3. [Datenbank-Schema](#datenbank-schema)
4. [backend.py – Eigene API-Routen](#backendpy--eigene-api-routen)
5. [frontend.js – Browser-Code](#frontendjs--browser-code)
6. [🔒 Plugin-Sicherheit](#-plugin-sicherheit)
7. [Plugin testen](#plugin-testen)
8. [Best Practices](#best-practices)
9. [Plugin veröffentlichen](#plugin-veröffentlichen)
10. [Troubleshooting](#troubleshooting)
11. [Sicherheitshinweis](#sicherheitshinweis)

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

**Minimales Beispiel** (nur frontend.js, kein Backend):

```json
// plugin.json
{
  "name": "Hallo Welt",
  "version": "1.0.0",
  "author": "DeinName",
  "description": "Zeigt einen Toast wenn auf Schaltfläche geklickt wird.",
  "verified": false,
  "enabled": true,
  "permissions": []
}
```

```javascript
// frontend.js
PluginAPI.addMenuItem('Hallo Welt', '👋', function() {
    showToast && showToast('👋 Hallo aus meinem Plugin!');
});
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
| `version` | string | – | Versionsnummer nach SemVer, z.B. `"1.2.0"` |
| `author` | string | – | Name des Entwicklers / GitHub-Username |
| `description` | string | – | Kurzbeschreibung (1–2 Sätze) |
| `verified` | bool | – | `false` = Plugin hat automatische Tests bestanden und ist im Marketplace verfügbar – wurde aber noch nicht persönlich vom Maintainer geprüft. `true` = Vom Maintainer persönlich geprüft und freigegeben (✅ Verifiziert-Badge). Wird ausschließlich vom Maintainer gesetzt, niemals selbst auf `true` setzen. |
| `enabled` | bool | – | `false` = Plugin wird beim Start nicht geladen |
| `permissions` | array | – | Liste der benötigten Berechtigungen (siehe [Permissions](#permissions-system)) |

> ⚠️ **Wichtig:** Das Feld heißt `"verified"`, nicht `"trusted"`. Letzteres wird ignoriert.

---

## Datenbank-Schema

Das Hauptsystem verwendet **SQLite**. Folgende Tabellen stehen Plugins zur Verfügung (mit passender Permission):

### `products` – Produkte *(Permission: `inventory.read` / `inventory.write`)*

| Spalte | Typ | Beschreibung |
|--------|-----|--------------|
| `id` | INTEGER | Primärschlüssel |
| `name` | TEXT | Produktname |
| `barcode` | TEXT | EAN/QR-Code (eindeutig) |
| `short` | TEXT | Kurzkürzel |
| `min_stock` | INTEGER | Mindestbestand (Benachrichtigungsschwelle) |

### `inventory` – Bestandsmengen *(Permission: `inventory.read` / `inventory.write`)*

| Spalte | Typ | Beschreibung |
|--------|-----|--------------|
| `id` | INTEGER | Primärschlüssel |
| `product_id` | INTEGER | FK → `products.id` |
| `location_id` | INTEGER | FK → `locations.id` |
| `quantity` | INTEGER | Aktuelle Menge |

### `locations` – Lagerorte *(Permission: `inventory.read`)*

| Spalte | Typ | Beschreibung |
|--------|-----|--------------|
| `id` | INTEGER | Primärschlüssel |
| `name` | TEXT | Name des Lagerorts |

### `users` – Benutzer *(Permission: `users.read` / `users.write`)*

| Spalte | Typ | Beschreibung |
|--------|-----|--------------|
| `id` | INTEGER | Primärschlüssel |
| `username` | TEXT | Benutzername (eindeutig) |
| `is_admin` | INTEGER | `1` = Admin, `0` = normaler Nutzer |

### `settings` – Einstellungen *(Permission: `system.settings`)*

| Spalte | Typ | Beschreibung |
|--------|-----|--------------|
| `key` | TEXT | Einstellungsschlüssel (eindeutig) |
| `value` | TEXT | Wert als JSON-String oder Plaintext |

> 💡 **Plugin-Daten** werden in eigenen Tabellen gespeichert (z.B. `mein_plugin_config`). Präfix mit Plugin-Name empfohlen, um Konflikte zu vermeiden.

### Häufige SQL-Abfragen

```python
# Alle Produkte mit aktuellem Bestand und Lagerort
conn = get_db_connection()
c = conn.cursor()
c.execute("""
    SELECT p.id, p.name, p.barcode, p.min_stock,
           COALESCE(l.name, 'Kein Ort') as ort,
           COALESCE(i.quantity, 0) as bestand
    FROM products p
    LEFT JOIN inventory i ON p.id = i.product_id
    LEFT JOIN locations l ON i.location_id = l.id
    ORDER BY p.name
""")
produkte = c.fetchall()
conn.close()

# Produkte unter Mindestbestand
c.execute("""
    SELECT p.name, p.min_stock, COALESCE(SUM(i.quantity), 0) as gesamt
    FROM products p
    LEFT JOIN inventory i ON p.id = i.product_id
    GROUP BY p.id
    HAVING gesamt < p.min_stock
""")
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
| `get_db_connection()` | Funktion | Gibt eine SQLite-Verbindung zurück (mit `row_factory`) |
| `require_auth()` | Decorator | Schützt Routen – prüft Session-Login |
| `json_response(obj, status)` | Funktion | Gibt JSON-Antwort zurück (orjson-optimiert); `status` optional, Standard `200` |
| `user_is_admin(name)` | Funktion | `True` wenn Benutzer Admin-Rechte hat |
| `get_setting_value(key)` | Funktion | Liest einen Wert aus der `settings`-Tabelle |
| `app` | Flask App | Die Flask-App-Instanz |
| `session` | Flask session | Aktuelles Session-Objekt (`session['user']` = Benutzername) |
| `request` | Flask request | Aktuelles Request-Objekt |
| `jsonify` | Funktion | Flask jsonify |
| `ADMIN_TOKEN` | string | Der konfigurierte Admin-Token (für Admin-API-Routen) |
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
@plugin_blueprint.route('/produkte', methods=['GET'])
@require_auth()
def produkte():
    conn = get_db_connection()
    c = conn.cursor()
    try:
        c.execute('SELECT id, name, barcode FROM products ORDER BY name')
        rows = c.fetchall()
        return json_response({'produkte': [dict(r) for r in rows]})
    except Exception as e:
        return json_response({'error': str(e)}, 500)
    finally:
        conn.close()  # Immer schließen, auch bei Fehler!
```

### Eigene DB-Tabellen anlegen

```python
def _init_plugin_tables():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS mein_plugin_daten (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        key TEXT UNIQUE NOT NULL,
        value TEXT,
        created INTEGER DEFAULT (strftime('%s','now'))
    )''')
    conn.commit()
    conn.close()

# Beim Blueprint-Start aufrufen
try:
    _init_plugin_tables()
except Exception as e:
    print(f'[mein-plugin] DB-Init Fehler: {e}')
```

### Einstellungen speichern / laden

```python
import json as json_module

SETTINGS_KEY = 'mein_plugin_settings'

def _load_settings():
    raw = get_setting_value(SETTINGS_KEY)
    if raw:
        try:
            return json_module.loads(raw)
        except Exception:
            pass
    return {'enabled': True, 'option_a': 'default'}  # Fallback

def _save_settings(data):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
              (SETTINGS_KEY, json_module.dumps(data)))
    conn.commit()
    conn.close()
```

### Auth schützen

```python
@plugin_blueprint.route('/admin-bereich', methods=['GET'])
@require_auth()
def admin_bereich():
    username = session.get('user', '')
    if not user_is_admin(username):
        return json_response({'error': 'Kein Zugriff'}, 403)
    return json_response({'geheim': 'Nur für Admins'})
```

### POST-Requests verarbeiten

```python
@plugin_blueprint.route('/speichern', methods=['POST'])
@require_auth()
def speichern():
    data = request.get_json(silent=True) or {}
    wert = data.get('wert', '').strip()
    if not wert:
        return json_response({'error': 'Kein Wert angegeben'}, 400)
    # ... verarbeiten ...
    return json_response({'status': 'ok'})
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

// Backend-API aufrufen (automatisch mit korrektem Präfix /api/plugin/{pluginId}/...)
const resp = await PluginAPI.fetch(pluginId, '/meine-route');
const data = await resp.json();

// POST-Request ans Backend
const resp = await PluginAPI.fetch(pluginId, '/speichern', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ wert: 'test' })
});
```

### Verfügbare Events

| Event | Wird ausgelöst wenn | Data |
|---|---|---|
| `bestand_geaendert` | Bestandsmenge geändert | `{ productKey, delta }` |
| `produkt_erstellt` | Neues Produkt angelegt | `{ productKey }` |
| `produkt_geloescht` | Produkt gelöscht | `{ productKey }` |
| `standort_gewechselt` | Benutzer wechselt Lagerort-Ansicht | `{ locationId }` |

> **Hinweis:** Events werden über `PluginAPI.emitEvent(...)` ausgelöst. Damit Hauptanwendungs-Events funktionieren, müssen die entsprechenden Stellen in `index.html` um `PluginAPI.emitEvent(...)` Aufrufe ergänzt werden.

### Modal erstellen

```javascript
function openMeinPluginModal() {
    const m = document.createElement('div');
    m.className = 'modal';
    m.style.display = 'flex';
    m.innerHTML = `
        <div class="modal-content" style="max-width:500px;width:95vw">
            <h3>🔌 Mein Plugin</h3>
            <div id="mein-plugin-inhalt">Lade...</div>
            <button class="btn" onclick="this.closest('.modal').remove()">Schließen</button>
        </div>
    `;
    document.body.appendChild(m);
    m.addEventListener('click', e => { if (e.target === m) m.remove(); });

    // Daten laden nach Modal-Öffnung
    ladeDaten();
}

async function ladeDaten() {
    try {
        const resp = await PluginAPI.fetch(pluginId, '/daten');
        const data = await resp.json();
        document.getElementById('mein-plugin-inhalt').textContent = JSON.stringify(data);
    } catch(e) {
        document.getElementById('mein-plugin-inhalt').textContent = 'Fehler: ' + e.message;
    }
}
```

### Globale Funktionen der Hauptanwendung

> ⚠️ Diese können sich mit Updates ändern. Nur stabile Kandidaten verwenden.

```javascript
showToast && showToast('✅ Erledigt!');         // Toast-Nachricht
showToast && showToast('❌ Fehler!', 'error');  // Toast als Fehler

const db = window.productDatabase || {};         // Produkt-DB (read-only)

openScannerSelectModal && openScannerSelectModal();  // Scanner öffnen
```

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
| `system.network` | Netzwerkzugriff (für externe HTTP-Requests) |
| `notifications.send` | Benachrichtigungen senden |
| `api.public` | Öffentliche API nutzen |
| `api.admin` | Admin-API nutzen |

**Default-Permissions für neue Plugins:**
```json
["db.read", "inventory.read", "api.public"]
```

**Verified-Plugins (nach persönlicher Prüfung durch den Maintainer):**
```json
["db.read", "db.write", "inventory.read", "inventory.write",
 "users.read", "notifications.send", "api.public", "api.admin"]
```

> 💡 Prinzip der minimalen Berechtigungen: Nur anfordern, was das Plugin wirklich braucht.

### Plugin-Signaturen (Ed25519)

Offizielle Plugins können kryptografisch signiert werden.

**Signatur erstellen (für Maintainer):**
```bash
# Private Key generieren (einmalig, sicher aufbewahren!)
python -c "from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey; \
import base64; key = Ed25519PrivateKey.generate(); \
print('Private:', base64.b64encode(key.private_bytes_raw()).decode()); \
print('Public:', base64.b64encode(key.public_key().public_bytes_raw()).decode())"
```

Die `plugin.sig` Datei enthält die base64-kodierte Ed25519-Signatur des Plugin-Inhalts.

### Audit-Logs

Alle Plugin-Aktionen werden protokolliert: Plugin geladen/entladen, API-Aufrufe, DB-Zugriffe, Konfigurationsänderungen.

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

| Muster | Grund |
|--------|-------|
| `os.system()` | Beliebige Befehlsausführung |
| `subprocess` | Prozessausführung |
| `eval()` / `exec()` | Dynamische Code-Ausführung |
| `socket` | Direkter Netzwerkzugriff |
| `shutil.rmtree` | Rekursives Löschen |
| `pickle` | Unsichere Deserialisierung (RCE-Risiko) |

```
GET /api/plugins/{plugin_id}/scan
```

---

## Plugin testen

Im Repository liegt ein `tests/`-Ordner mit Test-Infrastruktur. Plugins sollten vor dem PR getestet werden.

**Manuelle Checkliste vor Pull Request:**

- [ ] `plugin.json` valides JSON, Felder korrekt (besonders `"verified": false`)
- [ ] Backend-Routen mit `@require_auth()` geschützt wo nötig
- [ ] Alle DB-Verbindungen werden in `finally`-Block geschlossen
- [ ] Keine hardcodierten Tokens oder Passwörter im Code
- [ ] Permissions in `plugin.json` minimal gehalten
- [ ] `frontend.js` funktioniert ohne Konsolen-Fehler
- [ ] Plugin-Ordner-Name entspricht den Namensregeln

---

## Best Practices

### Python (backend.py)

```python
# ✅ Gut: Verbindung immer in try/finally schließen
def meine_route():
    conn = get_db_connection()
    try:
        c = conn.cursor()
        c.execute('SELECT ...')
        return json_response({'data': [dict(r) for r in c.fetchall()]})
    except Exception as e:
        return json_response({'error': 'Interner Fehler'}, 500)
    finally:
        conn.close()

# ✅ Gut: Benutzereingaben validieren
wert = request.get_json(silent=True) or {}
name = str(wert.get('name', '')).strip()[:100]  # Länge begrenzen
if not name:
    return json_response({'error': 'Name erforderlich'}, 400)

# ✅ Gut: Plugin-Settings mit Fallback laden
settings = json_module.loads(get_setting_value('mein_plugin') or '{}')
timeout = settings.get('timeout', 30)  # Default-Wert

# ❌ Schlecht: Keine Fehlerbehandlung
conn = get_db_connection()
c.execute('...')
conn.close()  # Wird bei Exception nie erreicht
```

### JavaScript (frontend.js)

```javascript
// ✅ Gut: Fehler fangen und dem Nutzer anzeigen
async function ladeData() {
    try {
        const resp = await PluginAPI.fetch(pluginId, '/daten');
        if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
        return await resp.json();
    } catch(e) {
        showToast && showToast('❌ Fehler: ' + e.message, 'error');
        return null;
    }
}

// ✅ Gut: Auf Hauptanwendungs-Funktionen prüfen bevor aufrufen
if (typeof showToast === 'function') showToast('✅ Gespeichert!');

// ❌ Schlecht: Globale Variablen ohne IIFE (wird durch IIFE-Wrapper verhindert,
//    aber innerhalb des eigenen Codes trotzdem var statt let/const vermeiden)
```

---

## Plugin veröffentlichen

1. Fork dieses Repositories: https://github.com/Gamerhund/lagersync-plugins
2. Erstelle einen neuen Ordner unter `plugins/` für dein Plugin
3. Füge deine Dateien hinzu: `plugin.json`, optionale `backend.py`, `frontend.js`
4. Stelle sicher, dass `"verified": false` in `plugin.json` gesetzt ist – **niemals selbst auf `true` setzen**
5. Erstelle einen Pull Request mit kurzer Beschreibung was das Plugin macht
6. Automatische Tests laufen durch – wenn bestanden, wird das Plugin in den Marketplace aufgenommen
7. Das Plugin erscheint zunächst **ohne Verified-Badge** (⏳ Ausstehend)
8. Der Maintainer prüft den Code in eigener Zeit – bei positiver Prüfung wird `"verified": true` gesetzt und das **✅ Verifiziert**-Badge erscheint

**Plugin-Ordner Namensregeln:**
- Nur: `a-z`, `A-Z`, `0-9`, `-`, `_`
- Keine Leerzeichen oder Sonderzeichen
- Lowercase empfohlen: `ki-assistent`, `low_stock_notifications`

---

## Troubleshooting

| Problem | Ursache | Lösung |
|---------|---------|--------|
| Plugin wird nicht geladen | `"enabled": false` in `plugin.json` | Auf `true` setzen |
| `403 Forbidden` bei API-Aufruf | Fehlende Permission | Permission in `plugin.json` ergänzen |
| `AttributeError: 'get_db_connection'` | Falsche Blueprint-Struktur | Sicherstellen dass `plugin_blueprint` korrekt benannt ist |
| `json.JSONDecodeError` beim Laden | Ungültige `plugin.json` | JSON-Validator verwenden (z.B. jsonlint.com) |
| Toast wird nicht angezeigt | Funktion noch nicht geladen | `showToast &&` Guard verwenden |
| Route nicht erreichbar | Falscher URL-Präfix | URL muss `/api/plugin/{ordner-name}/route` sein |
| DB-Connection leak | Fehlende `conn.close()` | `finally`-Block verwenden |

---

## Sicherheitshinweis

> 🔒 **Security-Level: 8-9/10** – Das Plugin-System verfügt über:
> - **Permissions System** – Plugins müssen Berechtigungen explizit anfordern
> - **Ed25519 Signaturen** – Offizielle Plugins sind kryptografisch signiert
> - **Audit-Logs** – Alle Aktionen werden protokolliert
> - **Rate Limiting** – API-Aufrufe sind pro Zeiteinheit begrenzt
> - **Code-Scanner** – Beim Laden wird auf gefährliche Muster geprüft

Alle Plugins im Marketplace haben automatische Tests bestanden. Plugins die noch nicht persönlich vom Maintainer geprüft wurden, sind mit **⏳ Ausstehend** gekennzeichnet. Persönlich geprüfte Plugins tragen das **✅ Verifiziert**-Badge (`"verified": true`, wird ausschließlich vom Maintainer gesetzt).

> ⚠️ **Trotz Sicherheitsmaßnahmen:** Installiere nur Plugins deren Quellcode du gelesen und verstanden hast. Externe Plugins können potenziell schädlichen Code enthalten, der nicht vom Scanner erkannt wird.

---

*Lizenz: MIT © 2026 Jonas (Gamerhund)*
