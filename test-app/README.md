# 🧩 Plugin-Test-Umgebung

Lokale Entwicklungsumgebung für LagerSync Plugins - teste Plugins ohne die Haupt-App zu beeinflussen. Die Test-Umgebung verhält sich genauso wie das echte Plugin-System und zeigt alle Fehlermeldungen an, damit du Plugins vollständig testen kannst.

## 🚀 Schnellstart

### 1. Abhängigkeiten installieren

```bash
cd test-env
pip install -r requirements.txt
```

### 2. Server starten

```bash
python server.py
```

### 3. Test-Umgebung öffnen

Öffne im Browser: http://localhost:8000

## 📋 Funktionen

### **Plugin-Management**
- ✅ Liste aller verfügbaren Plugins aus dem `plugins/` Ordner
- ✅ Plugins aktivieren/deaktivieren (wie im echten System)
- ✅ Plugin-Einstellungen anzeigen und testen
- ✅ Frontend-Code Vorschau und Ausführung
- ✅ Backend-Routen automatisch registrieren
- ✅ Fehlermeldungen bei Plugin-Ladefehlern (Backend/Frontend)

### **Test-Datenbank**
- 📦 Test-Produkte (mit Beständen und Min-Beständen)
- 📍 Test-Lagerorte (mit Kapazitäten)
- ✅ Simuliert die echte Datenbankstruktur

### **API-Endpunkte**

#### Plugin-Management
- `GET /api/plugins` - Liste aller Plugins
- `POST /api/plugins/<name>/activate` - Plugin aktivieren
- `POST /api/plugins/<name>/deactivate` - Plugin deaktivieren
- `GET /api/plugins/<name>/settings` - Plugin-Einstellungen

#### Test-Datenbank
- `GET /api/mock-data` - Alle Test-Daten
- `GET/POST /api/mock-data/products` - Produkte
- `GET/POST /api/mock-data/locations` - Lagerorte

## 🛠️ Eigenes Plugin testen

### 1. Plugin erstellen

Erstelle einen neuen Ordner unter `plugins/` (übergeordnet zum test-env):

```
lagersync-plugins/
├── plugins/
│   └── mein-test-plugin/
│       ├── plugin.json     # Pflicht
│       ├── backend.py      # Optional (Flask-Routen)
│       └── frontend.js     # Optional (Browser-UI)
└── test-env/
    └── server.py
```

### 2. plugin.json

```json
{
  "name": "Mein Test-Plugin",
  "version": "1.0.0",
  "author": "Dein Name",
  "description": "Beschreibung des Plugins",
  "verified": false,
  "enabled": false,
  "permissions": [
    "db.read",
    "db.write"
  ]
}
```

### 3. backend.py (Optional)

```python
def setup_routes(app, mock_data):
    """Registriert Plugin-spezifische API-Routen"""
    
    @app.route('/api/mein-test-plugin/action', methods=['POST'])
    def my_action():
        from flask import request
        data = request.json
        # Deine Logik hier
        return {'success': True, 'result': '...'}
```

### 4. frontend.js (Optional)

```javascript
function initMyPlugin() {
    console.log('Mein Plugin geladen');
    // UI-Code hier
}

// Plugin initialisieren
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initMyPlugin);
} else {
    initMyPlugin();
}
```

### 5. Testen

1. Server starten: `python server.py`
2. Browser öffnen: http://localhost:8000
3. Plugin in der Liste finden und aktivieren
4. Einstellungen öffnen und testen
5. Fehlermeldungen in der Konsole beachten

## 📁 Struktur

```
lagersync-plugins/
├── plugins/                  # Deine Plugins
│   ├── ki-assistent/
│   ├── low_stock_notifications/
│   ├── test-plugin/          # Beispiel-Plugin
│   └── dein-plugin/          # Dein neues Plugin
└── test-env/                 # Test-Umgebung
    ├── server.py              # Flask-Server
    ├── requirements.txt       # Python-Abhängigkeiten
    ├── templates/
    │   └── index.html        # Frontend
    └── README.md            # Diese Datei
```

## 🔧 Backend-Entwicklung

### Test-Daten im Plugin verwenden

```python
def setup_routes(app, mock_data):
    @app.route('/api/my-plugin/low-stock', methods=['GET'])
    def get_low_stock():
        low_stock = []
        for product_id, product in mock_data['products'].items():
            if product['stock'] < product['min_stock']:
                low_stock.append(product)
        return {'success': True, 'products': low_stock}
```

### Plugin-spezifische Routen

Alle Plugin-Routen werden automatisch unter `/api/<plugin-name>/` registriert, sobald das Plugin aktiviert wird.

## 🎨 Frontend-Entwicklung

### Auf Test-Daten zugreifen

```javascript
async function loadProducts() {
    const response = await fetch('/api/mock-data/products');
    const products = await response.json();
    console.log(products);
}
```

### Plugin-API aufrufen

```javascript
async function callPluginAPI() {
    const response = await fetch('/api/my-plugin/action', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({data: 'test'})
    });
    const result = await response.json();
    console.log(result);
}
```

## 🐛 Troubleshooting

### Plugin wird nicht geladen
- Prüfe ob `plugin.json` existiert und gültiges JSON ist
- Prüfe ob der Plugin-Ordner unter `plugins/` liegt
- Schau in die Server-Konsole für Fehlermeldungen

### Backend-Routen funktionieren nicht
- Stelle sicher dass `setup_routes(app, mock_data)` definiert ist
- Prüfe die Konsole auf Fehlermeldungen beim Plugin-Laden
- Backend-Fehler sind nicht kritisch - Plugin kann ohne Backend geladen werden

### Frontend wird nicht ausgeführt
- Prüfe ob die Initialisierungsfunktion aufgerufen wird
- Prüfe die Browser-Konsole auf JavaScript-Fehler
- Frontend-Fehler sind nicht kritisch - Plugin kann ohne Frontend geladen werden

### Fehlermeldungen in der Konsole
- Die Test-Umgebung zeigt alle Fehlermeldungen an (Backend- und Frontend-Ladefehler)
- Das ist gewollt - so siehst du ob dein Plugin korrekt geladen wird
- Backend-Fehler zeigen an, dass Abhängigkeiten fehlen oder der Code fehlerhaft ist

## 📚 Weiterführende Dokumentation

- [Plugin-Entwicklung](../docs/PLUGINS.md)
- [Plugin-Beispiele](../docs/EXAMPLES.md)
- [Plugin-Architektur](../docs/ARCHITECTURE.md)
- [Plugin-Sicherheit](../docs/SECURITY.md)

## 🤝 Beitrag

Wenn du die Test-Umgebung verbesserst, erstelle gerne einen Pull Request!
