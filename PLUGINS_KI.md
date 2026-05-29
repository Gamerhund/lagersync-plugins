# 🤖 LagerSync Plugin-Entwicklung – KI-Version (Vibe Coding)

> **Liebe KI,** diese Datei ist speziell für dich aufbereitet.
> Lies sie vollständig bevor du anfängst Code zu schreiben.
> Alle Regeln unten sind Pflicht – nicht optional.

---

## Regeln – unbedingt beachten

1. `"verified": false` in `plugin.json` – **immer**. Niemals `true` setzen. Das macht nur der Maintainer.
2. `plugin_blueprint` muss exakt so heißen – der Plugin-Loader erwartet diesen Namen.
3. Alle DB-Verbindungen in `try/finally` schließen – sonst Connection-Leak.
4. Nur Permissions anfordern, die das Plugin wirklich braucht.
5. Backend-Routen die Nutzerdaten zeigen mit `@require_auth()` absichern.
6. Plugin-Ordnername: nur `a-z`, `0-9`, `-`, `_`, keine Leerzeichen.
7. Kein `os.system()`, `subprocess`, `eval()`, `exec()`, `socket`, `pickle` – wird vom Code-Scanner geblockt.

---

## Pflicht-Tests die bei jedem PR laufen

Im `tests/`-Ordner laufen automatisch folgende Checks – dein Plugin muss alle bestehen:

| Test | Was wird geprüft |
|------|-----------------|
| `test_plugin_structure.py` | `plugin.json` vorhanden, gültiges JSON, alle Pflichtfelder, SemVer-Format, Ordnername lowercase |
| `test_plugin_permissions.py` | Nur gültige Permissions, `permissions` ist ein Array |
| `test_plugin_verified.py` | `verified` ist boolean, `author`/`description` nicht leer, **`verified` ist `false`** |
| `test_plugin_files.py` | `backend.py` valides Python, `plugin_blueprint` vorhanden, `frontend.js` nicht leer |
| `test_plugin_signature.py` | Verifizierte Plugins haben gültige Ed25519-Signatur |

**Der wichtigste Test:** `test_new_plugins_must_not_self_verify` – schlägt fehl wenn `"verified": true` in einem neuen Plugin steht.

---

## Dateistruktur

```
plugins/
└── dein-plugin-name/
    ├── plugin.json     ← Pflicht
    ├── plugin.sig      ← Nur für verifizierte Plugins (Maintainer setzt das)
    ├── backend.py      ← Optional: Flask-API-Routen
    └── frontend.js     ← Optional: Browser-Code
```

---

## plugin.json – Minimal-Template

```json
{
  "name": "Plugin-Anzeigename",
  "version": "1.0.0",
  "author": "GitHub-Username",
  "description": "Was das Plugin macht (1-2 Sätze).",
  "verified": false,
  "enabled": true,
  "permissions": ["inventory.read"]
}
```

**Alle Felder sind Pflicht** (`name`, `version`, `author`, `description`, `verified`, `enabled`). `permissions` kann leer sein `[]`.

---

## Verfügbare Permissions

```
db.read, db.write
inventory.read, inventory.write, inventory.delete
users.read, users.write
system.settings, system.files.read, system.files.write, system.network
notifications.send
api.public, api.admin
```

---

## Injizierte Variablen in backend.py (kein Import nötig)

```python
get_db_connection()        # SQLite-Verbindung mit row_factory
require_auth()             # Decorator – prüft Session-Login
json_response(obj, status) # JSON-Antwort, status optional (default 200)
user_is_admin(name)        # True wenn Admin
get_setting_value(key)     # Wert aus settings-Tabelle
app, session, request, jsonify, ADMIN_TOKEN, os, json
```

`session['user']` = aktueller Benutzername.

---

## Datenbank-Schema

### products *(inventory.read/write)*
`id`, `name`, `barcode` (eindeutig), `short`, `min_stock`

### inventory *(inventory.read/write)*
`id`, `product_id` → products, `location_id` → locations, `quantity`

### locations *(inventory.read)*
`id`, `name`

### users *(users.read/write)*
`id`, `username` (eindeutig), `is_admin` (1/0)

### settings *(system.settings)*
`key` (eindeutig), `value` (JSON-String oder Text)

**Plugin-eigene Tabellen:** Präfix mit Plugin-Name, z.B. `mein_plugin_config`.

---

## backend.py – Vollständiges Beispiel

```python
from flask import Blueprint
plugin_blueprint = Blueprint('mein_plugin', __name__)

# Eigene Tabellen anlegen
def _init():
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

try:
    _init()
except Exception as e:
    print(f'[mein-plugin] DB-Init Fehler: {e}')

# Route mit Auth
@plugin_blueprint.route('/daten', methods=['GET'])
@require_auth()
def get_daten():
    conn = get_db_connection()
    try:
        c = conn.cursor()
        c.execute('SELECT id, name, barcode FROM products ORDER BY name')
        rows = c.fetchall()
        return json_response({'produkte': [dict(r) for r in rows]})
    except Exception as e:
        return json_response({'error': str(e)}, 500)
    finally:
        conn.close()  # IMMER in finally!

# POST-Route
@plugin_blueprint.route('/speichern', methods=['POST'])
@require_auth()
def speichern():
    data = request.get_json(silent=True) or {}
    wert = str(data.get('wert', '')).strip()[:200]
    if not wert:
        return json_response({'error': 'Kein Wert'}, 400)
    return json_response({'status': 'ok'})
```

---

## frontend.js – Vollständiges Beispiel

```javascript
// pluginId = Ordnername des Plugins (automatisch verfügbar)

PluginAPI.addMenuItem('Mein Plugin', '🔌', async function() {
    const m = document.createElement('div');
    m.className = 'modal';
    m.style.display = 'flex';
    m.innerHTML = `
        <div class="modal-content" style="max-width:500px;width:95vw">
            <h3>🔌 Mein Plugin</h3>
            <div id="mp-inhalt">Lade...</div>
            <button class="btn" onclick="this.closest('.modal').remove()">Schließen</button>
        </div>`;
    document.body.appendChild(m);
    m.addEventListener('click', e => { if (e.target === m) m.remove(); });

    try {
        const resp = await PluginAPI.fetch(pluginId, '/daten');
        if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
        const data = await resp.json();
        document.getElementById('mp-inhalt').textContent = JSON.stringify(data, null, 2);
    } catch(e) {
        document.getElementById('mp-inhalt').textContent = 'Fehler: ' + e.message;
        showToast && showToast('❌ ' + e.message, 'error');
    }
});

// Events
PluginAPI.onEvent('bestand_geaendert', ({ productKey, delta }) => {
    console.log('[mein-plugin] Bestand geändert:', productKey, delta);
});
```

**Verfügbare Events:** `bestand_geaendert {productKey, delta}`, `produkt_erstellt {productKey}`, `produkt_geloescht {productKey}`, `standort_gewechselt {locationId}`

**Globale Funktionen (mit Guard aufrufen):**
```javascript
showToast && showToast('✅ Text');           // Toast normal
showToast && showToast('❌ Text', 'error'); // Toast Fehler
const db = window.productDatabase || {};    // Produkt-DB read-only
openScannerSelectModal && openScannerSelectModal();
```

---

## Routen-URL-Schema

```
/api/plugin/{ordner-name}/{route}
```

Beispiel: Ordner `rechnungs-export`, Route `/erstellen` → `/api/plugin/rechnungs-export/erstellen`

---

## PR-Checkliste (vor dem Erstellen prüfen)

- `"verified": false` in plugin.json
- `plugin_blueprint` korrekt benannt
- Alle DB-Verbindungen in try/finally
- `@require_auth()` auf Routen mit Nutzerdaten
- Permissions minimal gehalten
- Keine gefährlichen Muster (os.system, subprocess, eval, exec, socket, pickle)
- Ordnername: lowercase, kein Leerzeichen, nur `a-z 0-9 - _`
- Alle Pflichtfelder in plugin.json vorhanden

---

*Für die menschenlesbare Version siehe [PLUGINS.md](PLUGINS.md)*
*Lizenz: MIT © 2026 Jonas (Gamerhund)*
