import os
import sys
import json
import re
import importlib.util
from flask import Flask, render_template, jsonify, request, send_from_directory
from flask_cors import CORS

PLUGINS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'plugins'))
sys.path.insert(0, PLUGINS_DIR)

app = Flask(__name__)
CORS(app)

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

loaded_plugins = {}
active_plugins = {}

def get_safe_plugin_path(plugin_name):
    if not isinstance(plugin_name, str) or not plugin_name:
        raise ValueError("Ungültiger Plugin-Name")
    if not re.fullmatch(r"[A-Za-z0-9_-]+", plugin_name):
        raise ValueError("Ungültiger Plugin-Name")
    candidate_path = os.path.abspath(os.path.realpath(os.path.join(PLUGINS_DIR, plugin_name)))
    if os.path.commonpath([os.path.abspath(os.path.realpath(PLUGINS_DIR)), candidate_path]) != os.path.abspath(os.path.realpath(PLUGINS_DIR)):
        raise ValueError("Ungültiger Plugin-Name")
    canonical_name = os.path.basename(candidate_path)
    if not re.fullmatch(r"[A-Za-z0-9_-]+", canonical_name):
        raise ValueError("Ungültiger Plugin-Name")
    return candidate_path, canonical_name

def get_safe_plugin_json_path(plugin_name):
    plugin_path = get_safe_plugin_path(plugin_name)
    plugin_json_path = os.path.abspath(os.path.realpath(os.path.join(plugin_path, 'plugin.json')))
    if os.path.commonpath([plugin_path, plugin_json_path]) != plugin_path:
        raise ValueError("Ungültiger Plugin-Pfad")
    return plugin_json_path

class SafeFlaskWrapper:
    def __init__(self, app, plugin_name):
        self._app = app
        self._plugin_name = plugin_name

    def route(self, rule, **options):
        if not rule.startswith(f"/api/plugins/{self._plugin_name}"):
            raise ValueError(f"Plugin darf nur Routen unter /api/plugins/{self._plugin_name} registrieren")
        endpoint = options.get('endpoint')
        if endpoint:
            options['endpoint'] = f"plugin_{self._plugin_name}_{endpoint}"
        return self._app.route(rule, **options)

    def add_url_rule(self, rule, endpoint=None, view_func=None, **options):
        if not rule.startswith(f"/api/plugins/{self._plugin_name}"):
            raise ValueError(f"Plugin darf nur Routen unter /api/plugins/{self._plugin_name} registrieren")
        if endpoint:
            endpoint = f"plugin_{self._plugin_name}_{endpoint}"
        self._app.add_url_rule(rule, endpoint, view_func, **options)

    def __getattr__(self, name):
        return getattr(self._app, name)

def load_plugin(plugin_name):
    try:
        plugin_path, canonical_plugin_name = get_safe_plugin_path(plugin_name)
        plugin_name = canonical_plugin_name
    except ValueError as e:
        return None, str(e)

    plugins_root = os.path.abspath(os.path.realpath(PLUGINS_DIR))
    plugin_path = os.path.abspath(os.path.realpath(plugin_path))
    if os.path.commonpath([plugins_root, plugin_path]) != plugins_root:
        return None, "Ungültiger Plugin-Pfad"

    if not os.path.isdir(plugin_path):
        return None, "Plugin-Verzeichnis nicht gefunden"
    
    try:
        plugin_json_path = get_safe_plugin_json_path(plugin_name)
    except ValueError:
        return None, "Ungültiger Plugin-Pfad"
    if not os.path.exists(plugin_json_path):
        return None, "plugin.json nicht gefunden"
    
    try:
        with open(plugin_json_path, 'r', encoding='utf-8') as f:
            plugin_config = json.load(f)
    except Exception:
        app.logger.exception("Fehler beim Laden von plugin.json")
        return None, "Fehler beim Laden von plugin.json"
    
    backend_module = None
    backend_path = os.path.join(plugin_path, 'backend.py')
    if os.path.isfile(backend_path):
        try:
            spec = importlib.util.spec_from_file_location(f"{plugin_name}_backend", backend_path)
            backend_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(backend_module)
        except Exception:
            app.logger.exception("Backend konnte nicht geladen werden")
            backend_module = None
    
    frontend_code = None
    frontend_path = os.path.join(plugin_path, 'frontend.js')
    if os.path.exists(frontend_path):
        try:
            with open(frontend_path, 'r', encoding='utf-8') as f:
                frontend_code = f.read()
        except Exception:
            app.logger.exception("Frontend konnte nicht geladen werden")
            frontend_code = None
    
    plugin_info = {
        'config': plugin_config,
        'backend': backend_module,
        'frontend': frontend_code,
        'path': plugin_path
    }
    
    return plugin_info, None

def get_all_plugins():
    plugins = []
    if not os.path.exists(PLUGINS_DIR):
        return plugins
    
    for item in os.listdir(PLUGINS_DIR):
        try:
            plugin_path = get_safe_plugin_path(item)
        except ValueError:
            continue
        if os.path.isdir(plugin_path) and not item.startswith('_'):
            plugin_json_path = os.path.join(plugin_path, 'plugin.json')
            if os.path.exists(plugin_json_path):
                try:
                    with open(plugin_json_path, 'r', encoding='utf-8') as f:
                        config = json.load(f)
                    plugins.append({
                        'name': item,
                        'config': config,
                        'loaded': item in loaded_plugins,
                        'active': item in active_plugins
                    })
                except Exception:
                    pass
    return plugins

@app.route('/')
def index():
    return render_template('index.html', plugins=get_all_plugins())

@app.route('/api/plugins')
def api_plugins():
    return jsonify(get_all_plugins())

@app.route('/api/plugins/<plugin_name>/load', methods=['POST'])
def api_load_plugin(plugin_name):
    try:
        plugin_path, canonical_plugin_name = get_safe_plugin_path(plugin_name)
    except ValueError:
        return jsonify({'success': False, 'error': 'Ungültiger Plugin-Name'}), 400
        
    if canonical_plugin_name in loaded_plugins:
        return jsonify({'success': True, 'message': 'Plugin bereits geladen'})
    
    plugin_info, error = load_plugin(canonical_plugin_name)
    if error:
        return jsonify({'success': False, 'error': 'Konnte Plugin nicht laden'}), 400
    
    loaded_plugins[canonical_plugin_name] = plugin_info
    return jsonify({'success': True, 'message': f'Plugin {canonical_plugin_name} geladen'})

@app.route('/api/plugins/<plugin_name>/activate', methods=['POST'])
def api_activate_plugin(plugin_name):
    try:
        plugin_path, canonical_plugin_name = get_safe_plugin_path(plugin_name)
        plugin_name = canonical_plugin_name
    except ValueError:
        return jsonify({'success': False, 'error': 'Ungültiger Plugin-Name'}), 400
        
    try:
        if plugin_name not in loaded_plugins:
            plugin_info, error = load_plugin(plugin_name)
            if error:
                try:
                    plugin_json_path = get_safe_plugin_json_path(plugin_name)
                except ValueError:
                    return jsonify({'success': False, 'error': 'Konnte Plugin nicht laden'}), 400
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
                    except Exception:
                        app.logger.exception("Fehler beim Fallback-Laden")
                        return jsonify({'success': False, 'error': 'Konnte Plugin nicht laden'}), 400
                else:
                    return jsonify({'success': False, 'error': 'Konnte Plugin nicht laden: plugin.json nicht gefunden'}), 400
            else:
                loaded_plugins[plugin_name] = plugin_info
        
        active_plugins[plugin_name] = loaded_plugins[plugin_name]
        create_plugin_routes()
        return jsonify({'success': True, 'message': f'Plugin {plugin_name} aktiviert'})
    except Exception:
        app.logger.exception("Fehler beim Aktivieren des Plugins")
        return jsonify({'success': False, 'error': 'Unerwarteter interner Fehler'}), 400

@app.route('/api/plugins/<plugin_name>/deactivate', methods=['POST'])
def api_deactivate_plugin(plugin_name):
    try:
        plugin_path = get_safe_plugin_path(plugin_name)
    except ValueError:
        return jsonify({'success': False, 'error': 'Ungültiger Plugin-Name'}), 400
        
    if plugin_name in active_plugins:
        del active_plugins[plugin_name]
    return jsonify({'success': True, 'message': f'Plugin {plugin_name} deaktiviert'})

@app.route('/api/plugins/<plugin_name>/settings', methods=['GET'])
def api_plugin_settings(plugin_name):
    try:
        plugin_path = get_safe_plugin_path(plugin_name)
    except ValueError:
        return jsonify({'success': False, 'error': 'Ungültiger Plugin-Name'}), 400
        
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
    return jsonify(MOCK_DATA)

def is_request_local():
    return request.remote_addr in ('127.0.0.1', '::1', 'localhost')

@app.route('/api/mock-data/products', methods=['GET', 'POST'])
def api_mock_products():
    if request.method == 'POST':
        if not is_request_local():
            return jsonify({'success': False, 'error': 'Forbidden'}), 403
        data = request.json
        if not isinstance(data, dict):
            return jsonify({'success': False, 'error': 'Ungültige Daten'}), 400
        for k, v in data.items():
            if not isinstance(k, str) or not re.fullmatch(r"prod_[a-zA-Z0-9_-]+", k):
                return jsonify({'success': False, 'error': 'Ungültiger Produkt-ID-Format'}), 400
            if not isinstance(v, dict):
                return jsonify({'success': False, 'error': 'Ungültige Daten'}), 400
            if 'name' in v and not isinstance(v['name'], str):
                return jsonify({'success': False, 'error': 'Ungültiger Name'}), 400
            if 'stock' in v and not isinstance(v['stock'], int):
                return jsonify({'success': False, 'error': 'Ungültiger Bestand'}), 400
            if 'min_stock' in v and not isinstance(v['min_stock'], int):
                return jsonify({'success': False, 'error': 'Ungültiger Mindestbestand'}), 400
            if 'location' in v and not isinstance(v['location'], str):
                return jsonify({'success': False, 'error': 'Ungültiger Lagerort'}), 400
        MOCK_DATA['products'].update(data)
        return jsonify({'success': True})
    return jsonify(MOCK_DATA['products'])

@app.route('/api/mock-data/locations', methods=['GET', 'POST'])
def api_mock_locations():
    if request.method == 'POST':
        if not is_request_local():
            return jsonify({'success': False, 'error': 'Forbidden'}), 403
        data = request.json
        if not isinstance(data, dict):
            return jsonify({'success': False, 'error': 'Ungültige Daten'}), 400
        for k, v in data.items():
            if not isinstance(k, str) or not re.fullmatch(r"regal_[a-zA-Z0-9_-]+", k):
                return jsonify({'success': False, 'error': 'Ungültiger Lagerort-ID-Format'}), 400
            if not isinstance(v, dict):
                return jsonify({'success': False, 'error': 'Ungültige Daten'}), 400
            if 'name' in v and not isinstance(v['name'], str):
                return jsonify({'success': False, 'error': 'Ungültiger Name'}), 400
            if 'capacity' in v and not isinstance(v['capacity'], int):
                return jsonify({'success': False, 'error': 'Ungültige Kapazität'}), 400
        MOCK_DATA['locations'].update(data)
        return jsonify({'success': True})
    return jsonify(MOCK_DATA['locations'])

def create_plugin_routes():
    for plugin_name, plugin_info in active_plugins.items():
        if plugin_info['backend']:
            try:
                if hasattr(plugin_info['backend'], 'setup_routes'):
                    safe_app = SafeFlaskWrapper(app, plugin_name)
                    plugin_info['backend'].setup_routes(safe_app, MOCK_DATA)
            except Exception:
                app.logger.exception("Fehler beim Setup der Routes")

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8000, debug=True)
