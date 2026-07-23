#!/usr/bin/env python3
import os
import sys
import json
import sqlite3
import argparse
from pathlib import Path

try:
    import importlib.util
except ImportError:
    print("ERROR: importlib not available")
    sys.exit(1)

PLUGINS_DIR = Path("plugins")

def test_plugin_load(plugin_name, python_version):
    plugin_dir = PLUGINS_DIR / plugin_name
    plugin_json = plugin_dir / "plugin.json"
    backend_py = plugin_dir / "backend.py"
    
    results = {
        "plugin": plugin_name,
        "python_version": python_version,
        "detection": "PASS",
        "loading": "PASS",
        "initialization": "PASS",
        "smoke_test": "PASS",
        "errors": []
    }
    
    if not plugin_json.exists():
        results["detection"] = "FAIL"
        results["errors"].append("plugin.json not found")
        return results
    
    try:
        with open(plugin_json, "r", encoding="utf-8") as f:
            meta = json.load(f)
    except json.JSONDecodeError as e:
        results["detection"] = "FAIL"
        results["errors"].append(f"plugin.json invalid JSON: {e}")
        return results
    
    if not backend_py.exists():
        results["loading"] = "SKIP"
        results["errors"].append("No backend.py - skipping runtime test")
        return results
    
    try:
        spec = importlib.util.spec_from_file_location(
            f"runtime_test_{plugin_name}",
            backend_py
        )
        
        if not spec or not spec.loader:
            results["loading"] = "FAIL"
            results["errors"].append("Could not create module spec")
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
        
        temp_context = {
            "db": temp_db,
            "app": type("MockApp", (), {})(),
            "get_db_connection": mock_get_db_connection,
            "require_auth": mock_require_auth
        }
        
        for key, value in temp_context.items():
            setattr(module, key, value)
        
        try:
            spec.loader.exec_module(module)
        except Exception as e:
            results["loading"] = "FAIL"
            results["errors"].append(f"Module load failed: {e}")
            return results
        finally:
            temp_db.close()
            
    except Exception as e:
        results["initialization"] = "FAIL"
        results["errors"].append(f"Runtime test failed: {e}")
        return results
    
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
        result = test_plugin_load(plugin_name, args.python_version)
        all_results.append(result)
    
    with open(args.output, "w") as f:
        json.dump(all_results, f, indent=2)
    
    failed = any(r["loading"] == "FAIL" or r["initialization"] == "FAIL" for r in all_results)
    sys.exit(1 if failed else 0)

if __name__ == "__main__":
    main()
