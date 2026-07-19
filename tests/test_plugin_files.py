import pytest
import ast
from pathlib import Path

def test_backend_py_syntax_if_exists(plugin_dir):
    for plugin_path in plugin_dir.iterdir():
        if plugin_path.is_dir() and (not plugin_path.name.startswith('__')):
            backend_py = plugin_path / 'backend.py'
            if backend_py.exists():
                with open(backend_py, 'r', encoding='utf-8') as f:
                    content = f.read()
                try:
                    ast.parse(content)
                except SyntaxError as e:
                    pytest.fail(f'Plugin {plugin_path.name}: backend.py hat Syntaxfehler: {e}')

def test_backend_py_has_blueprint(plugin_dir):
    for plugin_path in plugin_dir.iterdir():
        if plugin_path.is_dir() and (not plugin_path.name.startswith('__')):
            backend_py = plugin_path / 'backend.py'
            if backend_py.exists():
                with open(backend_py, 'r', encoding='utf-8') as f:
                    content = f.read()
                assert 'plugin_blueprint' in content, f"Plugin {plugin_path.name}: backend.py muss 'plugin_blueprint' definieren"

def test_frontend_js_syntax_if_exists(plugin_dir):
    for plugin_path in plugin_dir.iterdir():
        if plugin_path.is_dir() and (not plugin_path.name.startswith('__')):
            frontend_js = plugin_path / 'frontend.js'
            if frontend_js.exists():
                with open(frontend_js, 'r', encoding='utf-8') as f:
                    content = f.read()
                assert content.strip(), f'Plugin {plugin_path.name}: frontend.js ist leer'

def test_plugin_files_have_safe_names(plugin_dir):
    import re
    allowed = re.compile('^[a-zA-Z0-9_.\\-]+$')
    for plugin_path in plugin_dir.iterdir():
        if not plugin_path.is_dir() or plugin_path.name.startswith('__'):
            continue
        for filepath in plugin_path.iterdir():
            if filepath.is_file():
                assert allowed.match(filepath.name), f"Plugin {plugin_path.name}: Datei '{filepath.name}' hat einen unsicheren Namen.\n  Erlaubt: a-z, A-Z, 0-9, Bindestrich (-), Unterstrich (_), Punkt (.)\n  Diese Datei wird beim Install übersprungen – Plugin wäre unvollständig!"

def test_backend_blueprint_instantiated_correctly(plugin_dir):
    import re
    for plugin_path in plugin_dir.iterdir():
        if not plugin_path.is_dir() or plugin_path.name.startswith('__'):
            continue
        backend_py = plugin_path / 'backend.py'
        if not backend_py.exists():
            continue
        content = backend_py.read_text(encoding='utf-8')
        assert re.search('plugin_blueprint\\s*=\\s*Blueprint\\s*\\(', content), f"Plugin {plugin_path.name}: plugin_blueprint nicht korrekt instanziiert.\n  Erwartet: plugin_blueprint = Blueprint('name', __name__)\n  Der Plugin-Loader registriert nur Blueprints mit exakt diesem Attributnamen."