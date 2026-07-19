"""
LagerSync Plugin-Test-Umgebung
Starte mit: python test-env/server.py
Zugriff unter: http://localhost:8000
"""

import os
import sys
import json
import importlib.util
from flask import Flask, render_template, jsonify, request, send_from_directory
from flask_cors import CORS

# Pfad zum plugins-Verzeichnis (übergeordnet)
PLUGINS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'plugins'))
sys.path.insert(0, PLUGINS_DIR)

app = Flask(__name__)
CORS(app)

# Mock-Daten für Tests
MOCK_DATA = {
    'products': {
        'prod_001': {'name': 'Schrauben M4', 'stock': 150, 'min_stock': 50, 'location': 'regal_a'},
        'prod_002': {'name': 'Muttern M4', 'stock': 25, 'min_stock': 100, 'location': 'regal_a'},
        'prod_003': {'name': 'Unterlegscheiben', 'stock': 500, 'min_stock': 200, 'location': 'regal_b'},
        'prod_004': {'name': 'Inbusschrauben M5', 'stock': 8, 'min_stock': 30, 'location': 'regal_c'},
    },
    'locations': {
        'regal_a': {'name': 'Regal A', 'capacity': 1000},
        'regal_b': {'name': 'Regal B', 'capacity': 500},
        'regal_c': {'name': 'Regal C', 'capacity': 300},
    },
    'settings': {
        'company_name': 'Test Firma GmbH',
        'currency': 'EUR',
        'language': 'de',
    }
}

# Geladene Plugins
loaded_plugins = {}
active_plugins = {}

def load_plugin(plugin_name):
    """Lädt ein Plugin aus dem plugins-Verzeichnis"""
    print(f"📦 Versuche Plugin zu laden: {plugin_name}")
    
    plugin_path = os.path.join(PLUGINS_DIR, plugin_name)
    
    if not os.path.exists(plugin_path):
        print(f"❌ Plugin-Verzeichnis nicht gefunden: {plugin_path}")
        return None, f"Plugin-Verzeichnis nicht gefunden: {plugin_path}"
    
    # plugin.json laden
    plugin_json_path = os.path.join(plugin_path, 'plugin.json')
    if not os.path.exists(plugin_json_path):
        print(f"❌ plugin.json nicht gefunden: {plugin_json_path}")
        return None, f"plugin.json nicht gefunden"
    
    try:
        with open(plugin_json_path, 'r', encoding='utf-8') as f:
            plugin_config = json.load(f)
        print(f"✅ plugin.json geladen: {plugin_config.get('name')}")
    except Exception as e:
        print(f"❌ Fehler beim Laden von plugin.json: {str(e)}")
        return None, f"Fehler beim Laden von plugin.json: {str(e)}"
    
    # Backend laden falls vorhanden
    backend_module = None
    backend_path = os.path.join(plugin_path, 'backend.py')
    if os.path.exists(backend_path):
        try:
            spec = importlib.util.spec_from_file_location(f"{plugin_name}_backend", backend_path)
            backend_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(backend_module)
            print(f"✅ Backend geladen")
        except Exception as e:
            # Backend-Fehler sind nicht kritisch - Plugin kann ohne Backend geladen werden
            print(f"⚠️ Backend konnte nicht geladen werden: {str(e)}")
            backend_module = None
    else:
        print(f"ℹ️ Kein backend.py vorhanden")
    
    # Frontend laden falls vorhanden
    frontend_code = None
    frontend_path = os.path.join(plugin_path, 'frontend.js')
    if os.path.exists(frontend_path):
        try:
            with open(frontend_path, 'r', encoding='utf-8') as f:
                frontend_code = f.read()
            print(f"✅ Frontend geladen ({len(frontend_code)} Zeichen)")
        except Exception as e:
            print(f"⚠️ Frontend konnte nicht geladen werden: {str(e)}")
            frontend_code = None
    else:
        print(f"ℹ️ Kein frontend.js vorhanden")
    
    plugin_info = {
        'config': plugin_config,
        'backend': backend_module,
        'frontend': frontend_code,
        'path': plugin_path
    }
    
    print(f"✅ Plugin {plugin_name} erfolgreich geladen")
    return plugin_info, None

def get_all_plugins():
    """Listet alle verfügbaren Plugins auf"""
    plugins = []
    if not os.path.exists(PLUGINS_DIR):
        return plugins
    
    for item in os.listdir(PLUGINS_DIR):
        plugin_path = os.path.join(PLUGINS_DIR, item)
        if os.path.isdir(plugin_path) and not item.startswith('_'):
            plugin_json_path = os.path.join(plugin_path, 'plugin.json')
            if os.path.exists(plugin_json_path):
                with open(plugin_json_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                plugins.append({
                    'name': item,
                    'config': config,
                    'loaded': item in loaded_plugins,
                    'active': item in active_plugins
                })
    return plugins

@app.route('/')
def index():
    """Hauptseite mit Plugin-Test-Umgebung"""
    return render_template('index.html', plugins=get_all_plugins())

@app.route('/api/plugins')
def api_plugins():
    """API: Liste aller Plugins"""
    return jsonify(get_all_plugins())

@app.route('/api/plugins/<plugin_name>/load', methods=['POST'])
def api_load_plugin(plugin_name):
    """API: Plugin laden"""
    if plugin_name in loaded_plugins:
        return jsonify({'success': True, 'message': 'Plugin bereits geladen'})
    
    plugin_info, error = load_plugin(plugin_name)
    if error:
        return jsonify({'success': False, 'error': error}), 400
    
    loaded_plugins[plugin_name] = plugin_info
    return jsonify({'success': True, 'message': f'Plugin {plugin_name} geladen'})

@app.route('/api/plugins/<plugin_name>/activate', methods=['POST'])
def api_activate_plugin(plugin_name):
    """API: Plugin aktivieren"""
    try:
        if plugin_name not in loaded_plugins:
            plugin_info, error = load_plugin(plugin_name)
            if error:
                # Versuche es trotzdem ohne Backend/Frontend zu laden
                plugin_path = os.path.join(PLUGINS_DIR, plugin_name)
                plugin_json_path = os.path.join(plugin_path, 'plugin.json')
                if os.path.exists(plugin_json_path):
                    try:
                        with open(plugin_json_path, 'r', encoding='utf-8') as f:
                            plugin_config = json.load(f)
                        plugin_info = {
                            'config': plugin_config,
                            'backend': None,
                            'frontend': None,
                            'path': plugin_path
                        }
                        loaded_plugins[plugin_name] = plugin_info
                    except Exception as fallback_error:
                        return jsonify({'success': False, 'error': f'Konnte Plugin nicht laden: {error} (Fallback: {fallback_error})'}), 400
                else:
                    return jsonify({'success': False, 'error': f'Konnte Plugin nicht laden: {error} (plugin.json nicht gefunden)'}), 400
            else:
                # Plugin erfolgreich geladen - zu loaded_plugins hinzufügen
                loaded_plugins[plugin_name] = plugin_info
        
        active_plugins[plugin_name] = loaded_plugins[plugin_name]
        
        # Routes neu erstellen
        create_plugin_routes()
        
        return jsonify({'success': True, 'message': f'Plugin {plugin_name} aktiviert'})
    except Exception as e:
        return jsonify({'success': False, 'error': f'Unerwarteter Fehler: {str(e)}'}), 400

@app.route('/api/plugins/<plugin_name>/deactivate', methods=['POST'])
def api_deactivate_plugin(plugin_name):
    """API: Plugin deaktivieren"""
    if plugin_name in active_plugins:
        del active_plugins[plugin_name]
    return jsonify({'success': True, 'message': f'Plugin {plugin_name} deaktiviert'})

@app.route('/api/plugins/<plugin_name>/settings', methods=['GET'])
def api_plugin_settings(plugin_name):
    """API: Plugin-Einstellungen abrufen"""
    if plugin_name not in active_plugins:
        return jsonify({'success': False, 'error': 'Plugin nicht aktiv'}), 400
    
    plugin_info = active_plugins[plugin_name]
    return jsonify({
        'success': True,
        'config': plugin_info['config'],
        'frontend': plugin_info['frontend']
    })

@app.route('/api/mock-data')
def api_mock_data():
    """API: Mock-Daten für Tests"""
    return jsonify(MOCK_DATA)

@app.route('/api/mock-data/products', methods=['GET', 'POST'])
def api_mock_products():
    """API: Produkt-Daten (lesen/schreiben)"""
    if request.method == 'POST':
        data = request.json
        MOCK_DATA['products'].update(data)
        return jsonify({'success': True})
    return jsonify(MOCK_DATA['products'])

@app.route('/api/mock-data/locations', methods=['GET', 'POST'])
def api_mock_locations():
    """API: Lagerort-Daten (lesen/schreiben)"""
    if request.method == 'POST':
        data = request.json
        MOCK_DATA['locations'].update(data)
        return jsonify({'success': True})
    return jsonify(MOCK_DATA['locations'])

# Plugin-spezifische API-Routen dynamisch erstellen
def create_plugin_routes():
    """Erstellt API-Routen für aktive Plugins"""
    for plugin_name, plugin_info in active_plugins.items():
        if plugin_info['backend']:
            try:
                # Prüfe ob das Plugin eine setup_routes Funktion hat
                if hasattr(plugin_info['backend'], 'setup_routes'):
                    plugin_info['backend'].setup_routes(app, MOCK_DATA)
                    print(f"✅ Routes für {plugin_name} erstellt")
            except Exception as e:
                print(f"⚠️ Fehler beim Setup der Routes für {plugin_name}: {e}")

if __name__ == '__main__':
    print("=" * 60)
    print("🧩 LagerSync Plugin-Test-Umgebung")
    print("=" * 60)
    print(f"📁 Plugins-Verzeichnis: {PLUGINS_DIR}")
    print(f"🌐 Server läuft unter: http://localhost:8000")
    print(f"📋 Verfügbare Plugins: {len(get_all_plugins())}")
    print("=" * 60)
    print("\nVerfügbare Plugins:")
    for plugin in get_all_plugins():
        status = "✅" if plugin['loaded'] else "⚪"
        print(f"  {status} {plugin['name']} - {plugin['config']['name']}")
    print("\nDrücke STRG+C zum Beenden")
    print("=" * 60)
    
    app.run(host='127.0.0.1', port=8000, debug=True)
