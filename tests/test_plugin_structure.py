import pytest
import json
from pathlib import Path

def test_all_plugins_have_plugin_json(plugin_dir):
    for plugin_path in plugin_dir.iterdir():
        if plugin_path.is_dir() and (not plugin_path.name.startswith('__')):
            plugin_json = plugin_path / 'plugin.json'
            assert plugin_json.exists(), f'Plugin {plugin_path.name} hat keine plugin.json'

def test_plugin_json_valid_json(plugin_dir):
    for plugin_path in plugin_dir.iterdir():
        if plugin_path.is_dir() and (not plugin_path.name.startswith('__')):
            plugin_json = plugin_path / 'plugin.json'
            with open(plugin_json, 'r', encoding='utf-8') as f:
                try:
                    json.load(f)
                except json.JSONDecodeError as e:
                    pytest.fail(f'plugin.json in {plugin_path.name} ist kein gültiges JSON: {e}')

def test_plugin_json_required_fields(plugin_dir):
    required_fields = ['name', 'version', 'author', 'description', 'verified', 'enabled']
    for plugin_path in plugin_dir.iterdir():
        if plugin_path.is_dir() and (not plugin_path.name.startswith('__')):
            plugin_json = plugin_path / 'plugin.json'
            with open(plugin_json, 'r', encoding='utf-8') as f:
                data = json.load(f)
            for field in required_fields:
                assert field in data, f"Plugin {plugin_path.name}: Pflichtfeld '{field}' fehlt"

def test_plugin_name_not_empty(plugin_dir):
    for plugin_path in plugin_dir.iterdir():
        if plugin_path.is_dir() and (not plugin_path.name.startswith('__')):
            plugin_json = plugin_path / 'plugin.json'
            with open(plugin_json, 'r', encoding='utf-8') as f:
                data = json.load(f)
            assert data.get('name'), f'Plugin {plugin_path.name}: name ist leer'
            assert len(data.get('name', '')) > 0, f'Plugin {plugin_path.name}: name ist leer'

def test_plugin_version_format(plugin_dir):
    import re
    for plugin_path in plugin_dir.iterdir():
        if plugin_path.is_dir() and (not plugin_path.name.startswith('__')):
            plugin_json = plugin_path / 'plugin.json'
            with open(plugin_json, 'r', encoding='utf-8') as f:
                data = json.load(f)
            version = data.get('version', '')
            assert re.match('^\\d+\\.\\d+\\.\\d+$', version), f"Plugin {plugin_path.name}: version '{version}' hat nicht das Format X.Y.Z"

def test_plugin_folder_name_lowercase(plugin_dir):
    for plugin_path in plugin_dir.iterdir():
        if plugin_path.is_dir() and (not plugin_path.name.startswith('__')):
            assert plugin_path.name == plugin_path.name.lower(), f'Plugin-Ordner {plugin_path.name} sollte lowercase sein'

def test_plugin_folder_name_no_spaces(plugin_dir):
    for plugin_path in plugin_dir.iterdir():
        if plugin_path.is_dir() and (not plugin_path.name.startswith('__')):
            assert ' ' not in plugin_path.name, f'Plugin-Ordner {plugin_path.name} darf keine Leerzeichen enthalten'

def test_plugin_folder_name_valid_chars(plugin_dir):
    import re
    for plugin_path in plugin_dir.iterdir():
        if plugin_path.is_dir() and (not plugin_path.name.startswith('__')):
            assert re.match('^[a-zA-Z0-9_-]+$', plugin_path.name), f"\n\n  ❌  Plugin-Ordner '{plugin_path.name}' enthält ungültige Zeichen.\n\n  Erlaubt: a-z, A-Z, 0-9, Bindestrich (-), Unterstrich (_)\n  Nicht erlaubt: Leerzeichen, Punkte, Sonderzeichen, Umlaute\n\n  Dieser Name wird beim Installieren vom Server abgelehnt.\n  Fix: Ordner umbenennen z.B. 'mein-plugin' oder 'mein_plugin'\n"