import pytest
import json
import sys
from pathlib import Path
try:
    from conftest import MAINTAINER_VERIFIED_PLUGINS
except ModuleNotFoundError:
    sys.path.insert(0, str(Path(__file__).parent.parent / '.github'))
    from verified_plugins import MAINTAINER_VERIFIED_PLUGINS

def test_verified_field_is_boolean(plugin_dir):
    for plugin_path in plugin_dir.iterdir():
        if plugin_path.is_dir() and (not plugin_path.name.startswith('__')):
            plugin_json = plugin_path / 'plugin.json'
            with open(plugin_json, 'r', encoding='utf-8') as f:
                data = json.load(f)
            verified = data.get('verified')
            assert isinstance(verified, bool), f'Plugin {plugin_path.name}: verified muss boolean sein, ist {type(verified)}'

def test_verified_plugins_have_author(plugin_dir):
    for plugin_path in plugin_dir.iterdir():
        if plugin_path.is_dir() and (not plugin_path.name.startswith('__')):
            plugin_json = plugin_path / 'plugin.json'
            with open(plugin_json, 'r', encoding='utf-8') as f:
                data = json.load(f)
            if data.get('verified'):
                author = data.get('author', '')
                assert author, f'Plugin {plugin_path.name}: Verifizierte Plugins müssen einen Autor haben'

def test_author_field_not_empty(plugin_dir):
    for plugin_path in plugin_dir.iterdir():
        if plugin_path.is_dir() and (not plugin_path.name.startswith('__')):
            plugin_json = plugin_path / 'plugin.json'
            with open(plugin_json, 'r', encoding='utf-8') as f:
                data = json.load(f)
            author = data.get('author', '')
            assert author, f'Plugin {plugin_path.name}: author darf nicht leer sein'
            assert len(author) > 0, f'Plugin {plugin_path.name}: author darf nicht leer sein'

def test_description_field_not_empty(plugin_dir):
    for plugin_path in plugin_dir.iterdir():
        if plugin_path.is_dir() and (not plugin_path.name.startswith('__')):
            plugin_json = plugin_path / 'plugin.json'
            with open(plugin_json, 'r', encoding='utf-8') as f:
                data = json.load(f)
            description = data.get('description', '')
            assert description, f'Plugin {plugin_path.name}: description darf nicht leer sein'
            assert len(description) > 0, f'Plugin {plugin_path.name}: description darf nicht leer sein'

def test_new_plugins_must_not_self_verify(plugin_dir):
    for plugin_path in plugin_dir.iterdir():
        if plugin_path.is_dir() and (not plugin_path.name.startswith('__')):
            if plugin_path.name in MAINTAINER_VERIFIED_PLUGINS:
                continue
            plugin_json = plugin_path / 'plugin.json'
            with open(plugin_json, 'r', encoding='utf-8') as f:
                data = json.load(f)
            verified = data.get('verified')
            assert verified is False, f"""\n\n  ❌  Plugin '{plugin_path.name}': verified darf nicht auf true gesetzt werden!\n\n  Das Feld wird ausschließlich vom Maintainer nach persönlicher\n  Prüfung des Quellcodes gesetzt. Dein Plugin erscheint zunächst\n  ohne Verified-Badge im Marketplace – das ist völlig normal.\n\n  Fix: Setze in deiner plugin.json:\n       "verified": false\n"""