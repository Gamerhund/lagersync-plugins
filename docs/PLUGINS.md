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
  "enabled": false,
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
| `verified` | bool | – | Wird **ausschließlich vom Maintainer** gesetzt – niemals selbst auf `true` setzen. `false` = Plugin hat automatische Tests bestanden und ist verfügbar. `true` + Ed25519-Signatur = vom Maintainer geprüft (✅ Badge), Details dazu in [SECURITY.md](SECURITY.md#wie-das-plugin-system-abgesichert-ist). |
| `enabled` | bool | – | Ob das Plugin nach der Installation sofort aktiv ist. Empfehlung: `false` (siehe unten, warum) |
| `permissions` | array | – | Liste der benötigten Berechtigungen (siehe unten) |

**Was nach der Installation passiert, hängt von `enabled` ab:**

- **`enabled: false` (empfohlen):** Dashboard → Marketplace → Installieren. Danach in den Einstellungen unter Plugins auf "Plugins neu laden" – das Plugin taucht auf, aber noch inaktiv. Erst nach manuellem Aktivieren + nochmal "neu laden" + Seite neu laden (Strg+R) ist es wirklich da (z.B. im Menü sichtbar). Etwas mehr Klicks, aber man sieht bewusst, was man gerade aktiviert, bevor es richtig losläuft.
- **`enabled: true`:** Nach der Installation reicht "Plugins neu laden" einmal, dann Seite neu laden – fertig, das Plugin ist sofort aktiv.

Beides ist technisch gültig, `test_plugin_structure.py` prüft nur, dass das Feld überhaupt ein Boolean ist. Für neue Einreichungen ist `false` der Default, weil so niemand versehentlich sofort mit unbekanntem Code arbeitet.

---

## Datenbank-Schema

Das System verwendet **SQLite**. Die Spaltenlisten unten sind die für Plugins relevanten Felder – kein vollständiger Schema-Dump (`products` hat z.B. noch mehr Spalten wie `price`, `category`, `notes`, ...).

> ⚠️ Drei Stellen weichen vom "naheliegenden" Namen ab – wer hier rät statt nachzuschauen, schreibt kaputtes SQL:
> - `locations` hat **kein** `id`-Feld – `name` selbst ist der Primärschlüssel (TEXT)
> - `inventory` referenziert den Lagerort über die Spalte **`location`** (TEXT, = `locations.name`), nicht `location_id`
> - `users` hat **kein** `is_admin`-Feld, sondern **`role`** (TEXT) – Admin-Check läuft über `user_is_admin(role_oder_name)` (siehe injizierte Variablen unten), nicht über einen Boolean

### `products` *(Permission: `inventory.read` / `inventory.write`)*

| Spalte | Typ | Beschreibung |
|--------|-----|--------------|
| `id` | INTEGER | Primärschlüssel |
| `name` | TEXT | Produktname |
| `barcode` | TEXT | EAN/QR-Code |
| `short` | TEXT | Kurzkürzel |
| `min_stock` | INTEGER | Mindestbestand |

### `inventory` *(Permission: `inventory.read` / `inventory.write`)*

| Spalte | Typ | Beschreibung |
|--------|-----|--------------|
| `location` | TEXT | FK → `locations.name` (**nicht** `location_id`) |
| `product_id` | INTEGER | FK → `products.id` |
| `quantity` | INTEGER | Aktuelle Menge |

Primärschlüssel ist die Kombination `(location, product_id)`.

### `locations` *(Permission: `inventory.read`)*

| Spalte | Typ | Beschreibung |
|--------|-----|--------------|
| `name` | TEXT | **Primärschlüssel** (kein separates `id`-Feld) |
| `color` | TEXT | Farbe für die UI |
| `is_group` | INTEGER | `1` = Gruppe statt einzelner Lagerort |

### `users` *(Permission: `users.read` / `users.write`)*

| Spalte | Typ | Beschreibung |
|--------|-----|--------------|
| `username` | TEXT | **Primärschlüssel** (kein separates `id`-Feld) |
| `role` | TEXT | z.B. `"admin"` – kein Boolean-Feld, siehe Hinweis oben |

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

### Plugin-Signaturen, Audit-Logs, Rate Limiting & Code-Scanner

Steht jetzt ausführlich in **[SECURITY.md](SECURITY.md)**, damit diese Datei API-Referenz bleibt und nicht ausartet. Kurzfassung: verifizierte Plugins werden Ed25519-signiert, jede Aktion landet im Audit-Log, API-Calls sind pro Permission rate-limitiert, und beim Laden wird der Code auf gefährliche Muster gescannt.

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

### Geplante Events (noch nicht verdrahtet)

`PluginAPI.emitEvent()`/`onEvent()` existieren bereits als Mechanismus in `index.html`. Die folgenden vier Event-Namen sind als Konvention vorgesehen, **werden aber aktuell von der Hauptanwendung selbst nirgends ausgelöst** – kein einziger der unten genannten `emitEvent()`-Aufrufe steckt heute in `index.html`. Bis das nachgezogen ist, kannst du dich nicht darauf verlassen, dass dein Plugin per `onEvent(...)` benachrichtigt wird, wenn z.B. der Bestand sich ändert.

| Event (geplant) | Soll ausgelöst werden wenn | Data |
|---|---|---|
| `bestand_geaendert` | Bestandsmenge geändert | `{ productKey, delta }` |
| `produkt_erstellt` | Neues Produkt angelegt | `{ productKey }` |
| `produkt_geloescht` | Produkt gelöscht | `{ productKey }` |
| `standort_gewechselt` | Benutzer wechselt Lagerort-Ansicht | `{ locationId }` |

**Was heute schon zuverlässig funktioniert:** eigene Events zwischen Plugins (`PluginAPI.emitEvent('mein_event', ...)` von Plugin A, `PluginAPI.onEvent('mein_event', ...)` in Plugin B) – das hängt nicht von der Hauptanwendung ab, siehe Beispiel oben. Verlass dich nur nicht auf die vier Events in der Tabelle, bis sie tatsächlich in `index.html` eingebaut sind.

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
  "enabled": false
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

**Mehr Beispiele:** [EXAMPLES.md](EXAMPLES.md) zeigt vier vollständige Plugins (Minimal, Backend-only, Frontend-only, Fullstack mit eigener DB-Tabelle, Tenant-Isolation und Error Handling) – oft hilfreicher zum Lernen als weitere Dokumentation.

---

## Plugin veröffentlichen (lagersync-plugins Repo)

Der vollständige Ablauf inkl. Branch-Namen und Review-Kriterien steht in [CONTRIBUTING.md](../CONTRIBUTING.md). Kurzfassung:

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
- Lowercase empfohlen: `ki-assistent`, `low_stock_notifications`, `mein-plugin`, `sso`

---

## Sicherheitshinweis

Das Plugin-System hat mehrere Schutzschichten (Permissions, Signaturen, Audit-Logs, Rate Limiting, Code-Scanner) – Details und wie man eine Lücke meldet stehen in [SECURITY.md](SECURITY.md).

Plugins ohne Verified-Badge wurden automatisch getestet, aber noch nicht persönlich geprüft. Das **✅ Verifiziert**-Badge (`"verified": true`) setzt ausschließlich der Maintainer, nach eigener Prüfung.

Trotzdem: Installier nur Plugins, deren Code du gelesen und verstanden hast. Der Scanner erkennt bekannte gefährliche Muster, nicht jede Art von schädlichem Code.

---

## ⚡ Performance-Optimierung

### Datenbank-Optimierung

```python
# ❌ Schlecht: N+1 Query Problem
@plugin_blueprint.route('/alle-produkte', methods=['GET'])
def schlechte_abfrage():
    conn = get_db_connection()
    c = conn.cursor()
    try:
        c.execute('SELECT id FROM products')
        products = c.fetchall()
        result = []
        for p in products:
            c.execute('SELECT * FROM inventory WHERE product_id = ?', (p['id'],))
            inv = c.fetchone()
            result.append({'product': p, 'inventory': inv})
        return json_response(result)
    finally:
        conn.close()

# ✅ Gut: JOIN Query
@plugin_blueprint.route('/alle-produkte', methods=['GET'])
def gute_abfrage():
    conn = get_db_connection()
    c = conn.cursor()
    try:
        c.execute('''
            SELECT p.*, i.quantity, i.location
            FROM products p
            LEFT JOIN inventory i ON p.id = i.product_id
        ''')
        return json_response(c.fetchall())
    finally:
        conn.close()
```

### Caching

```python
import time
from functools import lru_cache

# Einfaches In-Memory Caching
_cache = {}
_cache_ttl = {}

def get_cached(key, ttl_seconds, func):
    now = time.time()
    if key in _cache and now - _cache_ttl.get(key, 0) < ttl_seconds:
        return _cache[key]
    result = func()
    _cache[key] = result
    _cache_ttl[key] = now
    return result

@plugin_blueprint.route('/statistik', methods=['GET'])
def statistik():
    def calc_statistik():
        conn = get_db_connection()
        c = conn.cursor()
        try:
            c.execute('SELECT COUNT(*) as n FROM products')
            return c.fetchone()
        finally:
            conn.close()
    
    # Cache für 5 Minuten
    data = get_cached('statistik', 300, calc_statistik)
    return json_response(data)
```

### Lazy Loading

```javascript
// ❌ Schlecht: Alles auf einmal laden
PluginAPI.addMenuItem('Mein Plugin', '🔌', function() {
    // Lädt sofort alle Daten
    loadAllData();
    showModal();
});

// ✅ Gut: Lazy Loading
PluginAPI.addMenuItem('Mein Plugin', '🔌', function() {
    showModal(); // Erst UI zeigen
    setTimeout(() => loadAllData(), 100); // Dann Daten laden
});
```

### Asset-Optimierung

```javascript
// CSS/JS nur laden wenn nötig
if (document.querySelector('.inventory-page')) {
    // Nur auf Inventar-Seite laden
    loadPluginAssets();
}
```

---

## 🐛 Debugging

### Backend Debugging

```python
import logging

# Logging konfigurieren
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('mein_plugin')

@plugin_blueprint.route('/debug-test', methods=['GET'])
def debug_test():
    logger.debug('Debug-Test aufgerufen')
    logger.info('Info-Nachricht')
    logger.warning('Warnung')
    logger.error('Fehler')
    
    try:
        # Code der fehlschlagen könnte
        result = some_function()
        return json_response({'result': result})
    except Exception as e:
        logger.exception('Fehler in debug_test')
        return json_response({'error': str(e)}, 500)
```

### Frontend Debugging

```javascript
// Console Logging
console.log('[Mein Plugin] Initialisiert');
console.warn('[Mein Plugin] Warnung');
console.error('[Mein Plugin] Fehler');

// Error Boundary
window.addEventListener('error', function(e) {
    console.error('[Mein Plugin] Globaler Fehler:', e.error);
});

// Performance Tracking
console.time('mein-plugin-operation');
// ... Code ...
console.timeEnd('mein-plugin-operation');
```

### Plugin-Logs abrufen

`logging.basicConfig(level=logging.INFO)` in `lager-server.py` schreibt ohne `filename=`-Parameter nach **stdout/stderr**, nicht in eine feste Logdatei. Wo das landet, hängt davon ab, wie der Server läuft:

```bash
# Falls als systemd-Service eingerichtet:
journalctl -u <dein-service-name> -f

# Falls direkt im Terminal/Screen/tmux gestartet:
# einfach das Terminal-Fenster anschauen, in dem `python lager-server.py` läuft

# Frontend Logs (Browser Console)
# Öffne DevTools → Console
```

---

## 🧪 Testing

### Unit Tests für Backend

```python
# tests/test_mein_plugin.py
import unittest
import sqlite3
import tempfile
import os

class TestMeinPlugin(unittest.TestCase):
    def setUp(self):
        # Test-Datenbank erstellen
        self.db_fd, self.db_path = tempfile.mkstemp()
        self.conn = sqlite3.connect(self.db_path)
        self._init_test_db()
    
    def tearDown(self):
        self.conn.close()
        os.close(self.db_fd)
        os.unlink(self.db_path)
    
    def _init_test_db(self):
        # Test-Tabellen erstellen
        self.conn.execute('CREATE TABLE products (id INTEGER, name TEXT)')
        self.conn.commit()
    
    def test_plugin_function(self):
        # Test-Logik hier
        result = some_plugin_function(self.conn)
        self.assertEqual(result, expected_value)

if __name__ == '__main__':
    unittest.main()
```

### Frontend Tests

```javascript
// Einfache Funktionstests
function testPluginAPI() {
    console.assert(typeof PluginAPI !== 'undefined', 'PluginAPI nicht verfügbar');
    console.assert(typeof PluginAPI.addMenuItem === 'function', 'addMenuItem nicht verfügbar');
    console.log('✅ PluginAPI Tests bestanden');
}

// Im Browser Console ausführen
testPluginAPI();
```

---

## 📝 Error Handling & Logging

### Strukturiertes Logging

```python
import logging
import json
from datetime import datetime

logger = logging.getLogger('mein_plugin')

def log_action(action, details):
    log_entry = {
        'timestamp': datetime.now().isoformat(),
        'plugin': 'mein_plugin',
        'action': action,
        'details': details
    }
    logger.info(json.dumps(log_entry))

@plugin_blueprint.route('/aktion', methods=['POST'])
def meine_aktion():
    try:
        log_action('aktion_start', {'user': session.get('user')})
        # ... Logik ...
        log_action('aktion_success', {})
        return json_response({'status': 'ok'})
    except Exception as e:
        log_action('aktion_error', {'error': str(e)})
        return json_response({'error': 'Interner Fehler'}, 500)
```

### User-Friendly Error Messages

```python
@plugin_blueprint.route('/daten', methods=['GET'])
def get_daten():
    try:
        # ... Logik ...
        return json_response(data)
    except ValueError as e:
        return json_response({'error': 'Ungültige Eingabe', 'details': str(e)}, 400)
    except PermissionError:
        return json_response({'error': 'Keine Berechtigung'}, 403)
    except Exception as e:
        # Im Prod-Mode keine Details loggen
        logger.exception('Unerwarteter Fehler')
        return json_response({'error': 'Interner Fehler'}, 500)
```

---

## 🏢 Multi-Tenant Best Practices

### Tenant-spezifische Daten

```python
@plugin_blueprint.route('/meine-daten', methods=['GET'])
@require_auth()
def get_tenant_daten():
    # Tenant-ID aus Session holen
    tenant_id = session.get('tenant_id')
    if not tenant_id:
        return json_response({'error': 'Kein Tenant'}, 401)
    
    conn = get_db_connection()
    c = conn.cursor()
    try:
        # Tenant-spezifische Daten abfragen
        c.execute('''
            SELECT * FROM mein_plugin_daten
            WHERE tenant_id = ?
        ''', (tenant_id,))
        return json_response(c.fetchall())
    finally:
        conn.close()
```

### Tenant-Isolation sicherstellen

```python
# ❌ Schlecht: Cross-Tenant Zugriff möglich
@plugin_blueprint.route('/alle-daten', methods=['GET'])
def get_all_daten():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT * FROM mein_plugin_daten')  # Ohne tenant_id Filter!
    return json_response(c.fetchall())

# ✅ Gut: Tenant-Isolation
@plugin_blueprint.route('/meine-daten', methods=['GET'])
@require_auth()
def get_my_daten():
    tenant_id = session.get('tenant_id')
    conn = get_db_connection()
    c = conn.cursor()
    try:
        c.execute('''
            SELECT * FROM mein_plugin_daten
            WHERE tenant_id = ?
        ''', (tenant_id,))
        return json_response(c.fetchall())
    finally:
        conn.close()
```

---

## 📦 Versionierung & Migration

### SemVer verwenden

```json
{
  "version": "1.2.3"
}
```

- **MAJOR** (1.x.x): Breaking Changes
- **MINOR** (x.1.x): Neue Features, rückwärtskompatibel
- **PATCH** (x.x.1): Bugfixes, rückwärtskompatibel

### Datenbank-Migration

```python
def migrate_db(from_version, to_version):
    conn = get_db_connection()
    c = conn.cursor()
    try:
        if from_version < '1.1.0':
            # Migration zu 1.1.0
            c.execute('ALTER TABLE mein_plugin_daten ADD COLUMN new_field TEXT')
        
        if from_version < '1.2.0':
            # Migration zu 1.2.0
            c.execute('CREATE INDEX idx_tenant ON mein_plugin_daten(tenant_id)')
        
        conn.commit()
    finally:
        conn.close()

# Beim Plugin-Start aufrufen
# Hinweis: get_setting_value() ist injiziert (siehe oben), zum Schreiben gibt
# es aber keine eigene Funktion - das macht man wie die Hauptanwendung selbst
# auch, direkt per SQL.
current_version = get_setting_value('mein_plugin_version') or '1.0.0'
if current_version < '1.2.0':
    migrate_db(current_version, '1.2.0')
    conn = get_db_connection()
    try:
        conn.execute(
            'INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)',
            ('mein_plugin_version', '1.2.0')
        )
        conn.commit()
    finally:
        conn.close()
```

---

## 🔧 Troubleshooting

### Häufige Probleme

**Plugin wird nicht geladen:**
- Prüfe ob `plugin.json` gültiges JSON ist
- Prüfe ob `plugin_blueprint` in `backend.py` existiert
- Prüfe ob `verified: false` gesetzt ist

**Backend-Routen nicht erreichbar:**
- URL-Präfix ist `/api/plugin/{plugin-ordner-name}/`
- Prüfe ob Route mit `@plugin_blueprint.route()` dekoriert ist

**Frontend nicht geladen:**
- Prüfe ob `frontend.js` nicht leer ist
- Prüfe Browser Console auf JavaScript-Fehler

**Datenbank-Fehler:**
- Prüfe ob DB-Verbindung in `try/finally` geschlossen wird
- Prüfe ob Permissions korrekt gesetzt sind

### Performance-Probleme

**Plugin langsam:**
- Prüfe auf N+1 Query Probleme
- Verwende Caching für häufige Abfragen
- Lazy Loading für große Datenmengen

**Frontend langsam:**
- Prüfe auf unnötige DOM-Operationen
- Verwende Event-Debouncing
- Lazy Loading für Assets

---

## 🔄 Development Workflow

### Lokale Entwicklung

1. Plugin-Ordner in `plugins/` erstellen
2. `plugin.json`, `backend.py`, `frontend.js` erstellen
3. Server starten: `python lager-server.py`
4. Plugin im Dashboard testen
5. Logs überwachen

### Testing

```bash
# Alle Tests laufen lassen
pytest tests/ -v

# Nur eine bestimmte Test-Datei
pytest tests/test_plugin_structure.py -v
```

### Deployment

1. Alle Tests bestanden?
2. `verified: false` in `plugin.json`?
3. Pull Request erstellen
4. CI/CD Tests warten
5. Review durch Maintainer
6. Merge → Plugin im Marketplace

---

*Lizenz: MIT © 2026 Jonas (Gamerhund)*
