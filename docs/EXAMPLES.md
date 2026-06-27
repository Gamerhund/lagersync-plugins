# 📚 Examples

Vier Plugins, vom einfachsten zum komplexesten Fall, bewusst klein gehalten. Die echten Plugins in `plugins/` sind allesamt mehrere hundert Zeilen produktiver Code – gut als Referenz, aber zum Reinkommen eher ungeeignet. Hier sind die Bausteine einzeln, zum Abschauen.

Für die vollständige API-Referenz: [PLUGINS.md](PLUGINS.md). Für KI-Agenten die verdichtete Version: [PLUGINS_KI.md](PLUGINS_KI.md).

---

## 1. Minimal-Plugin (nur `plugin.json`)

Der einfachste mögliche Fall: ein Plugin ganz ohne eigenen Code, z.B. für ein reines Theme/Design oder eine Konfigurationsvorlage. So sieht z.B. `pro-design` aus.

```
plugins/mein-theme/
└── plugin.json
```

**plugin.json:**
```json
{
  "name": "Mein Theme",
  "version": "1.0.0",
  "author": "DeinName",
  "description": "Ein zusätzliches Farbschema ohne eigene Logik.",
  "verified": false,
  "enabled": false,
  "permissions": []
}
```

Kein `backend.py`, kein `frontend.js` nötig – `test_plugin_files.py` prüft diese nur, wenn sie existieren.

---

## 2. Backend-only Plugin (eigene API, keine UI)

Ein Plugin, das eine API-Route bereitstellt, aber keine eigene Browser-Oberfläche hat – z.B. für eine Integration, die nur von einem externen System abgefragt wird.

```
plugins/lagerbestand-api/
├── plugin.json
└── backend.py
```

**plugin.json:**
```json
{
  "name": "Lagerbestand-API",
  "version": "1.0.0",
  "author": "DeinName",
  "description": "Stellt den aktuellen Gesamtbestand als JSON-Endpunkt bereit.",
  "verified": false,
  "enabled": false,
  "permissions": ["inventory.read"]
}
```

**backend.py:**
```python
from flask import Blueprint

plugin_blueprint = Blueprint('lagerbestand_api', __name__)


@plugin_blueprint.route('/gesamtbestand', methods=['GET'])
@require_auth()
def gesamtbestand():
    """Gibt die Summe aller Bestände zurück (Permission: inventory.read)."""
    conn = get_db_connection()
    try:
        c = conn.cursor()
        c.execute('SELECT COALESCE(SUM(quantity), 0) AS gesamt FROM inventory')
        row = c.fetchone()
        return json_response({'gesamtbestand': row['gesamt']})
    except Exception as e:
        return json_response({'error': 'Interner Fehler'}, 500)
    finally:
        conn.close()
```

Erreichbar unter `/api/plugin/lagerbestand-api/gesamtbestand`.

---

## 3. Frontend-only Plugin (eigene UI, keine eigene API)

Ein Plugin, das nur die Browser-Oberfläche erweitert und ausschließlich mit Daten arbeitet, die die Hauptanwendung bereits global verfügbar macht (`window.productDatabase`) – ohne eigene Backend-Route.

```
plugins/schnellsuche/
├── plugin.json
└── frontend.js
```

**plugin.json:**
```json
{
  "name": "Schnellsuche",
  "version": "1.0.0",
  "author": "DeinName",
  "description": "Durchsucht die geladene Produkt-Datenbank per Tastenkürzel.",
  "verified": false,
  "enabled": false,
  "permissions": []
}
```

**frontend.js:**
```javascript
PluginAPI.addMenuItem('Schnellsuche', '🔍', function() {
    const begriff = prompt('Suchbegriff:');
    if (!begriff) return;

    const db = window.productDatabase || {};
    const treffer = Object.values(db).filter(p =>
        (p.name || '').toLowerCase().includes(begriff.toLowerCase())
    );

    if (treffer.length === 0) {
        showToast && showToast('Keine Treffer', 'error');
        return;
    }
    alert(treffer.map(p => `${p.name} (${p.barcode || 'kein Barcode'})`).join('\n'));
});
```

Da hier keine eigene API genutzt wird, ist `permissions: []` ausreichend – `window.productDatabase` ist clientseitig bereits geladen.

---

## 4. Fullstack-Plugin: Produktnotizen

Das vollständigste Beispiel: eigene Datenbank-Tabelle, GET/POST/DELETE-Routen, Tenant-Isolation, Auth-Schutz, Error Handling und ein Event an andere Plugins. Damit zeigt es alle Bausteine aus [PLUGINS.md](PLUGINS.md) und den KI-Regeln in [PLUGINS_KI.md](PLUGINS_KI.md) an einem zusammenhängenden Beispiel.

```
plugins/produktnotizen/
├── plugin.json
├── backend.py
└── frontend.js
```

**plugin.json:**
```json
{
  "name": "Produktnotizen",
  "version": "1.0.0",
  "author": "DeinName",
  "description": "Notizen zu einzelnen Produkten anlegen, anzeigen und löschen.",
  "verified": false,
  "enabled": false,
  "permissions": ["db.read", "db.write", "inventory.read"]
}
```

**backend.py:**
```python
from flask import Blueprint

plugin_blueprint = Blueprint('produktnotizen', __name__)


def _init_tables():
    conn = get_db_connection()
    try:
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS produktnotizen_eintraege (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tenant_id TEXT NOT NULL,
            barcode TEXT NOT NULL,
            text TEXT NOT NULL,
            erstellt INTEGER DEFAULT (strftime('%s','now'))
        )''')
        conn.commit()
    finally:
        conn.close()


try:
    _init_tables()
except Exception as e:
    print(f'[produktnotizen] DB-Init Fehler: {e}')


@plugin_blueprint.route('/notizen/<barcode>', methods=['GET'])
@require_auth()
def notizen_abrufen(barcode):
    """Alle Notizen zu einem Produkt – nur für den eigenen Tenant."""
    tenant_id = session.get('tenant_id')
    if not tenant_id:
        return json_response({'error': 'Kein Tenant'}, 401)

    conn = get_db_connection()
    try:
        c = conn.cursor()
        c.execute(
            'SELECT id, text, erstellt FROM produktnotizen_eintraege '
            'WHERE tenant_id = ? AND barcode = ? ORDER BY erstellt DESC',
            (tenant_id, barcode)
        )
        return json_response({'notizen': [dict(r) for r in c.fetchall()]})
    except Exception as e:
        return json_response({'error': 'Interner Fehler'}, 500)
    finally:
        conn.close()


@plugin_blueprint.route('/notizen/<barcode>', methods=['POST'])
@require_auth()
def notiz_erstellen(barcode):
    tenant_id = session.get('tenant_id')
    if not tenant_id:
        return json_response({'error': 'Kein Tenant'}, 401)

    data = request.get_json(silent=True) or {}
    text = str(data.get('text', '')).strip()[:500]
    if not text:
        return json_response({'error': 'Notiztext fehlt'}, 400)

    conn = get_db_connection()
    try:
        c = conn.cursor()
        c.execute(
            'INSERT INTO produktnotizen_eintraege (tenant_id, barcode, text) VALUES (?, ?, ?)',
            (tenant_id, barcode, text)
        )
        conn.commit()
        return json_response({'status': 'ok', 'id': c.lastrowid})
    except Exception as e:
        return json_response({'error': 'Interner Fehler'}, 500)
    finally:
        conn.close()


@plugin_blueprint.route('/notizen/<int:notiz_id>', methods=['DELETE'])
@require_auth()
def notiz_loeschen(notiz_id):
    tenant_id = session.get('tenant_id')
    if not tenant_id:
        return json_response({'error': 'Kein Tenant'}, 401)

    conn = get_db_connection()
    try:
        c = conn.cursor()
        # IMMER tenant_id mitprüfen – sonst könnte ein Tenant fremde Notizen löschen
        c.execute(
            'DELETE FROM produktnotizen_eintraege WHERE id = ? AND tenant_id = ?',
            (notiz_id, tenant_id)
        )
        conn.commit()
        if c.rowcount == 0:
            return json_response({'error': 'Nicht gefunden'}, 404)
        return json_response({'status': 'ok'})
    except Exception as e:
        return json_response({'error': 'Interner Fehler'}, 500)
    finally:
        conn.close()
```

**frontend.js:**
```javascript
async function ladeNotizen(barcode) {
    const liste = document.getElementById('pn-liste');
    liste.textContent = 'Lade...';
    try {
        const resp = await PluginAPI.fetch(pluginId, `/notizen/${barcode}`);
        if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
        const data = await resp.json();
        liste.innerHTML = data.notizen.length
            ? data.notizen.map(n => `<div class="pn-eintrag">${n.text}</div>`).join('')
            : '<em>Keine Notizen</em>';
    } catch (e) {
        liste.textContent = 'Fehler: ' + e.message;
        showToast && showToast('❌ Notizen konnten nicht geladen werden', 'error');
    }
}

function openProduktnotizenModal(barcode) {
    const m = document.createElement('div');
    m.className = 'modal';
    m.style.display = 'flex';
    m.innerHTML = `
        <div class="modal-content" style="max-width:500px;width:95vw">
            <h3>📝 Produktnotizen – ${barcode}</h3>
            <div id="pn-liste"></div>
            <input id="pn-input" type="text" maxlength="500" placeholder="Neue Notiz...">
            <button class="btn" id="pn-speichern">Speichern</button>
            <button class="btn" onclick="this.closest('.modal').remove()">Schließen</button>
        </div>`;
    document.body.appendChild(m);
    m.addEventListener('click', e => { if (e.target === m) m.remove(); });

    ladeNotizen(barcode);

    m.querySelector('#pn-speichern').addEventListener('click', async () => {
        const input = m.querySelector('#pn-input');
        const text = input.value.trim();
        if (!text) return;
        try {
            const resp = await PluginAPI.fetch(pluginId, `/notizen/${barcode}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ text }),
            });
            if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
            input.value = '';
            await ladeNotizen(barcode);
            PluginAPI.emitEvent('produktnotiz_erstellt', { barcode });
        } catch (e) {
            showToast && showToast('❌ Notiz konnte nicht gespeichert werden', 'error');
        }
    });
}

PluginAPI.addMenuItem('Produktnotizen', '📝', function() {
    const barcode = prompt('Barcode des Produkts:');
    if (barcode) openProduktnotizenModal(barcode);
});
```

**Was dieses Beispiel zeigt:**
- Eigene Tabelle mit `_init_tables()` beim Plugin-Start (siehe [PLUGINS.md](PLUGINS.md#eigene-db-tabellen-anlegen))
- `tenant_id` wird bei **jeder** Abfrage geprüft – auch beim Löschen, sonst könnte ein Tenant fremde Notizen löschen ([Multi-Tenant-Regeln](PLUGINS.md#-multi-tenant-best-practices))
- Jede Route ist mit `@require_auth()` geschützt
- Jede DB-Verbindung wird in `finally` geschlossen
- Fehler werden als JSON mit passendem HTTP-Status zurückgegeben statt als unbehandelte Exception
- Ein eigenes Event (`produktnotiz_erstellt`) wird ausgelöst, auf das andere Plugins reagieren könnten

---

## Welches Beispiel als Startpunkt?

| Du willst... | Start mit |
|---|---|
| Ein Theme oder eine reine Konfiguration | Beispiel 1 (Minimal) |
| Eine Integration ohne eigene UI (Webhook-Endpunkt, externe API) | Beispiel 2 (Backend-only) |
| Eine UI-Erweiterung, die nur mit bereits geladenen Daten arbeitet | Beispiel 3 (Frontend-only) |
| Etwas mit eigenen Daten, die Nutzer anlegen/ändern/löschen können | Beispiel 4 (Fullstack) |

Für komplexere, produktionsreife Referenzen schau dir die echten Plugins in `plugins/` an, insbesondere `low_stock_notifications` (mehrere Benachrichtigungskanäle) oder `sso` (OIDC-Integration).
