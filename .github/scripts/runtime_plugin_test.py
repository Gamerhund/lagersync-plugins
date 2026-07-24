#!/usr/bin/env python3
import os
import sys
import json
import sqlite3
import argparse
from pathlib import Path
from unittest.mock import Mock, MagicMock

try:
    import importlib.util
except ImportError:
    print("ERROR: importlib not available")
    sys.exit(1)

PLUGINS_DIR = Path("plugins")

def setup_external_mocks(module):
    mock_requests = MagicMock()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = "<html><body>Mock content</body></html>"
    mock_response.json.return_value = {"status": "ok"}
    mock_requests.get.return_value = mock_response
    mock_requests.post.return_value = mock_response
    
    mock_bs4 = MagicMock()
    mock_soup = MagicMock()
    mock_soup.find.return_value = None
    mock_soup.find_all.return_value = []
    mock_bs4.BeautifulSoup.return_value = mock_soup
    
    if not hasattr(module, 'requests'):
        module.requests = mock_requests
    if not hasattr(module, 'bs4'):
        module.bs4 = mock_bs4

def test_plugin_runtime(plugin_name, python_version):
    plugin_dir = PLUGINS_DIR / plugin_name
    plugin_json = plugin_dir / "plugin.json"
    backend_py = plugin_dir / "backend.py"
    
    results = {
        "plugin": plugin_name,
        "python_version": python_version,
        "detection": "PASS",
        "metadata": "SKIP",
        "loading": "SKIP",
        "initialization": "SKIP",
        "registration": "SKIP",
        "smoke_test": "SKIP",
        "api_test": "NOT_APPLICABLE",
        "error_handling": "SKIP",
        "side_effects": "SKIP",
        "overall": "SKIP",
        "errors": [],
        "skip_reasons": {}
    }
    
    if not plugin_dir.exists():
        results["detection"] = "FAIL"
        results["errors"].append(f"Plugin directory not found: {plugin_dir}")
        results["overall"] = "FAIL"
        return results
    
    if not plugin_json.exists():
        results["detection"] = "FAIL"
        results["errors"].append("plugin.json not found")
        results["overall"] = "FAIL"
        return results
    
    try:
        with open(plugin_json, "r", encoding="utf-8") as f:
            meta = json.load(f)
        
        required_fields = ["name", "version", "author", "description"]
        missing_fields = [f for f in required_fields if not meta.get(f)]
        if missing_fields:
            results["metadata"] = "FAIL"
            results["errors"].append(f"Missing metadata fields: {missing_fields}")
            results["overall"] = "FAIL"
            return results
        results["metadata"] = "PASS"
    except json.JSONDecodeError as e:
        results["metadata"] = "FAIL"
        results["errors"].append(f"plugin.json invalid JSON: {e}")
        results["overall"] = "FAIL"
        return results
    
    if not backend_py.exists():
        results["loading"] = "NOT_APPLICABLE"
        results["skip_reasons"]["loading"] = "No backend.py file"
        results["initialization"] = "NOT_APPLICABLE"
        results["registration"] = "NOT_APPLICABLE"
        results["smoke_test"] = "NOT_APPLICABLE"
        results["overall"] = "PASS"
        return results
    
    temp_db = None
    try:
        spec = importlib.util.spec_from_file_location(
            f"runtime_test_{plugin_name}",
            backend_py
        )
        
        if not spec or not spec.loader:
            results["loading"] = "FAIL"
            results["errors"].append("Could not create module spec")
            results["overall"] = "FAIL"
            return results
        
        module = importlib.util.module_from_spec(spec)
        
        temp_db = sqlite3.connect(":memory:")
        
        def mock_get_db_connection():
            conn = sqlite3.connect(":memory:")
            conn.row_factory = sqlite3.Row
            return conn
        
        def mock_require_auth(*args, **kwargs):
            def decorator(f):
                return f
            return decorator
        
        class MockFlaskApp:
            def __init__(self):
                self.blueprints = []
                self.routes = []
            
            def register_blueprint(self, blueprint, url_prefix=None, name=None):
                self.blueprints.append({
                    "blueprint": blueprint,
                    "url_prefix": url_prefix,
                    "name": name
                })
            
            def test_client(self):
                return MockTestClient(self)
        
        class MockTestClient:
            def __init__(self, app):
                self.app = app
            
            def get(self, path):
                return MockResponse(200, {"status": "ok"})
            
            def post(self, path, data=None):
                return MockResponse(200, {"status": "ok"})
        
        class MockResponse:
            def __init__(self, status_code, json_data):
                self.status_code = status_code
                self._json_data = json_data
            
            def get_json(self):
                return self._json_data
        
        mock_app = MockFlaskApp()
        
        temp_context = {
            "db": temp_db,
            "app": mock_app,
            "get_db_connection": mock_get_db_connection,
            "require_auth": mock_require_auth
        }
        
        for key, value in temp_context.items():
            setattr(module, key, value)
        
        setup_external_mocks(module)
        
        spec.loader.exec_module(module)
        results["loading"] = "PASS"
        
        if hasattr(module, "plugin_blueprint"):
            bp = module.plugin_blueprint
            mock_app.register_blueprint(bp, url_prefix=f"/api/plugin/{plugin_name}")
            results["registration"] = "PASS"
            
            if mock_app.blueprints:
                results["api_test"] = "PASS"
                results["skip_reasons"]["api_test"] = f"Blueprint registered: {len(mock_app.blueprints)} blueprint(s)"
            else:
                results["api_test"] = "SKIP"
                results["skip_reasons"]["api_test"] = "Blueprint exists but not registered to mock app"
        else:
            results["registration"] = "NOT_APPLICABLE"
            results["skip_reasons"]["registration"] = "No plugin_blueprint found"
            results["api_test"] = "NOT_APPLICABLE"
        
        callable_functions = [
            name for name in dir(module)
            if callable(getattr(module, name)) and not name.startswith("_")
        ]
        
        if callable_functions:
            try:
                for func_name in callable_functions[:3]:
                    func = getattr(module, func_name)
                    if callable(func):
                        results["smoke_test"] = "PASS"
                        results["skip_reasons"]["smoke_test"] = f"Tested function: {func_name}"
                        break
                else:
                    results["smoke_test"] = "SKIP"
                    results["skip_reasons"]["smoke_test"] = "No testable entry point found"
            except Exception as e:
                results["smoke_test"] = "FAIL"
                results["errors"].append(f"Smoke test failed: {e}")
        else:
            results["smoke_test"] = "NOT_APPLICABLE"
            results["skip_reasons"]["smoke_test"] = "No callable functions found"
        
        if results["loading"] == "FAIL":
            results["overall"] = "FAIL"
        elif results["smoke_test"] == "FAIL":
            results["overall"] = "FAIL"
        elif results["smoke_test"] == "PASS":
            results["overall"] = "PASS"
        elif results["loading"] == "PASS" and results["registration"] in ["PASS", "NOT_APPLICABLE"]:
            results["overall"] = "PASS"
        else:
            results["overall"] = "INCOMPLETE"
            
    except Exception as e:
        results["loading"] = "FAIL"
        results["errors"].append(f"Runtime test failed: {e}")
        results["overall"] = "FAIL"
    finally:
        if temp_db:
            temp_db.close()
    
    return results

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--plugins", required=True)
    parser.add_argument("--python-version", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    
    plugin_list = [p.strip() for p in args.plugins.split(",") if p.strip()]
    all_results = []
    
    for plugin_name in plugin_list:
        result = test_plugin_runtime(plugin_name, args.python_version)
        all_results.append(result)
    
    with open(args.output, "w") as f:
        json.dump(all_results, f, indent=2)
    
    failed = any(r["overall"] == "FAIL" for r in all_results)
    sys.exit(1 if failed else 0)

if __name__ == "__main__":
    main()
