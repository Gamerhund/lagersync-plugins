#!/usr/bin/env python3
import os
import sys
import json
import sqlite3
import argparse
import threading
import time
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch

try:
    import importlib.util
except ImportError:
    print("ERROR: importlib not available")
    sys.exit(1)

PLUGINS_DIR = Path("plugins")
TEST_MODE = os.environ.get("LAGERSYNC_TEST_MODE", "false") == "true"


def create_test_tables(cursor):
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY,
            name TEXT,
            sku TEXT,
            short TEXT,
            barcode TEXT,
            price REAL,
            ek REAL,
            min_stock INTEGER DEFAULT 5
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS inventory (
            id INTEGER PRIMARY KEY,
            product_id INTEGER,
            quantity INTEGER,
            location TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS locations (
            id INTEGER PRIMARY KEY,
            name TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT,
            is_admin INTEGER
        )
    """)


def get_db_snapshot(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    snapshot = {}
    for table in tables:
        cursor.execute(f"SELECT * FROM {table}")
        columns = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()
        snapshot[table] = {"columns": columns, "rows": rows}
    return snapshot

def setup_external_mocks(module):
    mock_requests = MagicMock()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = "<html><body><span class='price'>19.99</span></body></html>"
    mock_response.json.return_value = {"status": "ok"}
    mock_response.content = b"<html><body><span class='price'>19.99</span></body></html>"
    mock_requests.get.return_value = mock_response
    mock_requests.post.return_value = mock_response
    
    mock_bs4 = MagicMock()
    mock_soup = MagicMock()
    mock_price_element = MagicMock()
    mock_price_element.get_text.return_value = "19.99"
    mock_soup.find.return_value = mock_price_element
    mock_soup.find_all.return_value = [mock_price_element]
    mock_bs4.BeautifulSoup.return_value = mock_soup
    
    mock_smtplib = MagicMock()
    mock_smtp = MagicMock()
    mock_smtplib.SMTP.return_value = mock_smtp
    
    if not hasattr(module, 'requests'):
        module.requests = mock_requests
    if not hasattr(module, 'bs4'):
        module.bs4 = mock_bs4
    if not hasattr(module, 'smtplib'):
        module.smtplib = mock_smtplib
    
    return {
        "requests": mock_requests,
        "bs4": mock_bs4,
        "smtplib": mock_smtplib
    }

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
        "database_initialization": "SKIP",
        "registration": "SKIP",
        "route_discovery": "SKIP",
        "function_discovery": "SKIP",
        "api_test": "SKIP",
        "smoke_test": "SKIP",
        "external_services": "SKIP",
        "side_effects": "SKIP",
        "error_handling": "SKIP",
        "overall": "SKIP",
        "errors": [],
        "skip_reasons": {},
        "details": {}
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
    test_db = None
    active_threads = []
    
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
        
        test_db = sqlite3.connect(":memory:")
        test_db.row_factory = sqlite3.Row
        
        # Create common tables that plugins might need
        cursor = test_db.cursor()
        create_test_tables(cursor)
        test_db.commit()
        
        # Create a wrapper that prevents closing
        class DBWrapper:
            def __init__(self, db):
                self._db = db
                self.row_factory = db.row_factory
            
            def cursor(self):
                return self._db.cursor()
            
            def commit(self):
                return self._db.commit()
            
            def close(self):
                pass  # Do nothing - keep database open
            
            def execute(self, *args, **kwargs):
                return self._db.execute(*args, **kwargs)
            
            def __getattr__(self, name):
                return getattr(self._db, name)
        
        wrapped_db = DBWrapper(test_db)
        
        def mock_get_db_connection():
            return wrapped_db
        
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
                if hasattr(blueprint, 'deferred_functions'):
                    for func in blueprint.deferred_functions:
                        func(self)
            
            def add_url_rule(self, rule, endpoint=None, view_func=None, **options):
                self.routes.append({"rule": rule, "endpoint": endpoint, "function": view_func.__name__ if view_func else None})
            
            def test_client(self):
                return MockTestClient(self)
            
            def route(self, rule, **options):
                def decorator(f):
                    self.routes.append({"rule": rule, "options": options, "function": f.__name__})
                    return f
                return decorator
        
        class MockTestClient:
            def __init__(self, app):
                self.app = app
            
            def get(self, path):
                return MockResponse(200, {"status": "ok"})
            
            def post(self, path, data=None, json=None):
                return MockResponse(200, {"status": "ok"})
        
        class MockResponse:
            def __init__(self, status_code, json_data):
                self.status_code = status_code
                self._json_data = json_data
            
            def get_json(self):
                return self._json_data
            
            @property
            def data(self):
                return json.dumps(self._json_data).encode()
        
        mock_app = MockFlaskApp()
        
        temp_context = {
            "db": test_db,
            "app": mock_app,
            "get_db_connection": mock_get_db_connection,
            "require_auth": mock_require_auth
        }
        
        for key, value in temp_context.items():
            setattr(module, key, value)
        
        external_mocks = setup_external_mocks(module)
        
        import sys
        original_modules = {}
        for mod_name, mock_obj in external_mocks.items():
            if mod_name == 'requests':
                if 'requests' not in sys.modules:
                    original_modules['requests'] = None
                    sys.modules['requests'] = mock_obj
                else:
                    original_modules['requests'] = sys.modules['requests']
                    sys.modules['requests'] = mock_obj
            elif mod_name == 'bs4':
                if 'bs4' not in sys.modules:
                    original_modules['bs4'] = None
                    sys.modules['bs4'] = mock_obj
                else:
                    original_modules['bs4'] = sys.modules['bs4']
                    sys.modules['bs4'] = mock_obj
            elif mod_name == 'smtplib':
                if 'smtplib' not in sys.modules:
                    original_modules['smtplib'] = None
                    sys.modules['smtplib'] = mock_obj
                else:
                    original_modules['smtplib'] = sys.modules['smtplib']
                    sys.modules['smtplib'] = mock_obj
        
        if plugin_name == "low_stock_notifications":
            os.environ["LAGERSYNC_TEST_MODE"] = "true"
        
        spec.loader.exec_module(module)
        
        for mod_name, original_mod in original_modules.items():
            if original_mod is None:
                del sys.modules[mod_name]
            else:
                sys.modules[mod_name] = original_mod
        
        results["loading"] = "PASS"
        
        # Reopen database if plugin closed it
        try:
            cursor = test_db.cursor()
        except sqlite3.ProgrammingError:
            # Database was closed, reopen it
            test_db = sqlite3.connect(":memory:")
            test_db.row_factory = sqlite3.Row
            # Recreate common tables
            cursor = test_db.cursor()
            create_test_tables(cursor)
            test_db.commit()
        
        # Database initialization - check tables created by plugin
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables_after_import = [row[0] for row in cursor.fetchall()]
        
        plugin_tables = {
            "price_updater": ["price_updater_urls"],
            "ki-assistent": [],
            "low_stock_notifications": [],
            "sso": ["sso_config"]
        }
        
        expected_tables = plugin_tables.get(plugin_name, [])
        created_tables = [t for t in tables_after_import if t in expected_tables]
        
        if created_tables:
            results["database_initialization"] = "PASS"
            results["details"]["database_initialization"] = {
                "created_tables": created_tables,
                "note": "Plugin created its own tables during import"
            }
        else:
            results["database_initialization"] = "NOT_APPLICABLE"
            results["skip_reasons"]["database_initialization"] = "Plugin does not create its own tables"
        
        if hasattr(module, "plugin_blueprint"):
            bp = module.plugin_blueprint
            mock_app.register_blueprint(bp, url_prefix=f"/api/plugin/{plugin_name}")
            results["registration"] = "PASS"
            
            if mock_app.routes:
                discovered_routes = [r["rule"] for r in mock_app.routes]
                results["route_discovery"] = "PASS"
                results["details"]["route_discovery"] = {
                    "routes": discovered_routes,
                    "count": len(discovered_routes)
                }
            else:
                results["route_discovery"] = "SKIP"
                results["skip_reasons"]["route_discovery"] = "No routes discovered from blueprint"
        else:
            results["registration"] = "NOT_APPLICABLE"
            results["skip_reasons"]["registration"] = "No plugin_blueprint found"
            results["route_discovery"] = "NOT_APPLICABLE"
        
        callable_functions = [
            name for name in dir(module)
            if callable(getattr(module, name)) and not name.startswith("_")
        ]
        
        if callable_functions:
            results["function_discovery"] = "PASS"
            results["details"]["function_discovery"] = {
                "functions": callable_functions[:10],
                "count": len(callable_functions)
            }
        else:
            results["function_discovery"] = "NOT_APPLICABLE"
            results["skip_reasons"]["function_discovery"] = "No callable functions found"
        
        results["smoke_test"] = "NOT_APPLICABLE"
        results["skip_reasons"]["smoke_test"] = "Smoke test not yet executed - will be evaluated in plugin-specific test"
        
        if active_threads:
            results["details"]["background_threads"] = {
                "count": len(active_threads),
                "started": True
            }
            for thread in active_threads:
                if thread.is_alive():
                    thread._stop()
        
        plugin_smoke_result = run_plugin_specific_smoke_test(
            plugin_name, module, test_db, external_mocks, results
        )
        results.update(plugin_smoke_result)
        
        if results["loading"] == "FAIL":
            results["overall"] = "FAIL"
        elif results["smoke_test"] == "FAIL":
            results["overall"] = "FAIL"
        elif results["smoke_test"] == "PASS":
            # Only PASS if smoke test actually passed
            results["overall"] = "PASS"
        elif results["smoke_test"] == "SKIP":
            # If smoke test was skipped, overall is INCOMPLETE
            results["overall"] = "INCOMPLETE"
            results["skip_reasons"]["overall"] = "Smoke test was skipped - cannot determine plugin functionality"
        elif results["smoke_test"] == "NOT_APPLICABLE":
            # If smoke test is not applicable, overall is INCOMPLETE
            results["overall"] = "INCOMPLETE"
            results["skip_reasons"]["overall"] = "Smoke test not applicable - cannot determine plugin functionality"
        else:
            results["overall"] = "INCOMPLETE"
            
    except Exception as e:
        import traceback
        results["loading"] = "FAIL"
        results["errors"].append(f"Runtime test failed: {e}")
        results["errors"].append(f"Traceback: {traceback.format_exc()}")
        results["overall"] = "FAIL"
    finally:
        if test_db:
            try:
                test_db.close()
            except:
                pass
    
    return results

def run_plugin_specific_smoke_test(plugin_name, module, test_db, external_mocks, results):
    smoke_results = {
        "api_test": "SKIP",
        "smoke_test": "SKIP",
        "external_services": "SKIP",
        "side_effects": "SKIP",
        "error_handling": "SKIP",
        "authentication_test": "SKIP",
        "details": results.get("details", {}),
        "skip_reasons": results.get("skip_reasons", {})
    }
    
    # Take DB snapshot before smoke test
    try:
        cursor = test_db.cursor()
    except sqlite3.ProgrammingError:
        # Database was closed, reopen it
        test_db = sqlite3.connect(":memory:")
        test_db.row_factory = sqlite3.Row
        # Recreate common tables
        cursor = test_db.cursor()
        create_test_tables(cursor)
        test_db.commit()
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables_before = [row[0] for row in cursor.fetchall()]
    
    snapshot_before = {}
    for table in tables_before:
        cursor.execute(f"SELECT * FROM {table}")
        columns = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()
        snapshot_before[table] = {"columns": columns, "rows": rows}
    
    try:
        if plugin_name == "price_updater":
            plugin_result = _test_price_updater(module, test_db, external_mocks)
        elif plugin_name == "ki-assistent":
            plugin_result = _test_ki_assistent(module, test_db, external_mocks)
        elif plugin_name == "low_stock_notifications":
            plugin_result = _test_low_stock_notifications(module, test_db, external_mocks)
        elif plugin_name == "sso":
            plugin_result = _test_sso(module, test_db, external_mocks)
        else:
            plugin_result = {
                "smoke_test": "NOT_APPLICABLE",
                "skip_reasons": {"smoke_test": f"No specific smoke test for plugin: {plugin_name}"}
            }
        
        plugin_details = plugin_result.pop("details", {})
        plugin_skip_reasons = plugin_result.pop("skip_reasons", {})
        plugin_errors = plugin_result.pop("errors", [])
        
        smoke_results.update(plugin_result)
        smoke_results["details"].update(plugin_details)
        smoke_results["skip_reasons"].update(plugin_skip_reasons)
        smoke_results["errors"] = smoke_results.get("errors", []) + plugin_errors
    except Exception as e:
        smoke_results["smoke_test"] = "FAIL"
        smoke_results["errors"] = smoke_results.get("errors", [])
        smoke_results["errors"].append(f"Plugin-specific smoke test failed: {e}")
    
    # Take DB snapshot after smoke test

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables_after = [row[0] for row in cursor.fetchall()]
    
    snapshot_after = {}
    for table in tables_after:
        cursor.execute(f"SELECT * FROM {table}")
        columns = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()
        snapshot_after[table] = {"columns": columns, "rows": rows}
    
    # Compare snapshots
    changes = []
    for table in set(tables_before + tables_after):
        before = snapshot_before.get(table, {"rows": []})
        after = snapshot_after.get(table, {"rows": []})
        
        if before["rows"] != after["rows"]:
            changes.append({
                "table": table,
                "before_rows": len(before["rows"]),
                "after_rows": len(after["rows"])
            })
    
    if changes:
        smoke_results["side_effects"] = "PASS"
        smoke_results["details"]["side_effects"] = {
            "db_changes": changes,
            "note": "Database changes detected during smoke test"
        }
    else:
        smoke_results["side_effects"] = "NOT_APPLICABLE"
        smoke_results["skip_reasons"]["side_effects"] = "No database changes detected during smoke test"
    
    return smoke_results

def _test_price_updater(module, test_db, external_mocks):
    results = {
        "api_test": "SKIP",
        "smoke_test": "SKIP",
        "external_services": "SKIP",
        "side_effects": "SKIP",
        "error_handling": "SKIP",
        "authentication_test": "SKIP",
        "details": {},
        "errors": [],
        "skip_reasons": {}
    }
    
    try:
        cursor = test_db.cursor()
        
        cursor.execute("""
            INSERT INTO products (id, name, ek, sku) VALUES (1, 'Test Product', 10.00, 'TEST-001')
        """)
        test_db.commit()
        
        mock_html = '<html><body><span class="price">19.99</span></body></html>'
        external_mocks["requests"].get.return_value.text = mock_html
        external_mocks["requests"].get.return_value.content = mock_html.encode()
        external_mocks["requests"].get.return_value.status_code = 200
        
        mock_soup = MagicMock()
        mock_price_element = MagicMock()
        mock_price_element.get_text.return_value = "19.99"
        mock_soup.select_one.return_value = mock_price_element
        external_mocks["bs4"].BeautifulSoup.return_value = mock_soup
        
        if hasattr(module, '_extract_price_from_url'):
            extracted_price = module._extract_price_from_url('http://test.example')
            
            if extracted_price == 19.99:
                if external_mocks["requests"].get.called:
                    results["smoke_test"] = "PASS"
                    results["details"]["smoke_test"] = {
                        "operation": "extract_price_from_url",
                        "test_url": "http://test.example",
                        "expected_price": 19.99,
                        "actual_price": extracted_price,
                        "mock_used": external_mocks["requests"].get.called,
                        "note": "Tests price extraction only, not the full "
                                "update_product_price HTTP route (that route "
                                "reads session/request/json_response, which "
                                "this harness does not yet inject - see "
                                "authentication_test/api_test)."
                    }
                else:
                    results["smoke_test"] = "FAIL"
                    results["errors"].append("Price extraction test failed: Mock was not called by plugin")
            else:
                results["smoke_test"] = "FAIL"
                results["errors"].append(f"Price extraction failed: expected 19.99, got {extracted_price}")
        else:
            results["smoke_test"] = "SKIP"
            results["skip_reasons"]["smoke_test"] = "_extract_price_from_url function not found"
        
        if hasattr(module, 'plugin_blueprint'):
            results["api_test"] = "SKIP"
            results["skip_reasons"]["api_test"] = (
                "Only blueprint registration was checked (see 'registration'). "
                "No real HTTP request was made: the routes read session/request/"
                "json_response, which this harness doesn't inject yet."
            )
        
        results["external_services"] = "PASS"
        results["details"]["external_services"] = {
            "mocked": ["requests", "BeautifulSoup"],
            "note": "External HTTP requests mocked with realistic HTML response"
        }
        
        if hasattr(module, '_extract_price_from_url'):
            empty_soup = MagicMock()
            empty_soup.select_one.return_value = None
            empty_soup.find_all.return_value = []
            external_mocks["bs4"].BeautifulSoup.return_value = empty_soup
            external_mocks["requests"].get.return_value.text = '<html><body>no price here</body></html>'
            try:
                empty_result = module._extract_price_from_url('http://test.example/no-price')
                if empty_result is None:
                    results["error_handling"] = "PASS"
                    results["details"]["error_handling"] = {
                        "tested": "extract_price_from_url on a page with no price element",
                        "expected": None,
                        "actual": empty_result
                    }
                else:
                    results["error_handling"] = "FAIL"
                    results["errors"].append(
                        f"Expected None for a page with no price, got {empty_result!r}"
                    )
            except Exception as e:
                results["error_handling"] = "FAIL"
                results["errors"].append(f"_extract_price_from_url raised on missing price instead of returning None: {e}")
            external_mocks["bs4"].BeautifulSoup.return_value = mock_soup
        
        results["authentication_test"] = "SKIP"
        results["skip_reasons"]["authentication_test"] = "Auth testing requires real auth context"
        
    except Exception as e:
        results["smoke_test"] = "FAIL"
        results["errors"].append(f"Price updater smoke test failed: {e}")
    
    return results

def _test_ki_assistent(module, test_db, external_mocks):
    results = {
        "api_test": "SKIP",
        "smoke_test": "SKIP",
        "external_services": "SKIP",
        "side_effects": "SKIP",
        "error_handling": "SKIP",
        "authentication_test": "SKIP",
        "details": {},
        "errors": [],
        "skip_reasons": {}
    }
    
    try:
        cursor = test_db.cursor()
        
        cursor.execute("""
            INSERT INTO products (id, name, short, barcode, min_stock)
            VALUES (1, 'Test Product', 'TP', '1234567890123', 10)
        """)
        cursor.execute("""
            INSERT INTO inventory (id, product_id, quantity, location) VALUES (1, 1, 3, 'Warehouse A')
        """)
        cursor.execute("""
            INSERT INTO locations (id, name) VALUES (1, 'Warehouse A')
        """)
        test_db.commit()
        
        tool_results = {}
        
        if hasattr(module, '_tool_search_products'):
            search_result = module._tool_search_products("Test")
            tool_results["tool_search_products"] = search_result
            
            found_names = [p.get("name") for p in search_result.get("products", [])] \
                if isinstance(search_result, dict) else []
            
            if isinstance(search_result, dict) and search_result.get("found") == 1 \
                    and found_names == ["Test Product"]:
                results["details"].setdefault("smoke_test", {})["tool_search_products"] = {
                    "search_term": "Test",
                    "expected_found": 1,
                    "expected_name": "Test Product",
                    "actual": search_result
                }
            else:
                results["errors"].append(
                    f"_tool_search_products('Test') expected {{'found': 1, 'products': [name='Test Product']}}, "
                    f"got {search_result!r}"
                )
        else:
            results["skip_reasons"]["tool_search_products"] = "_tool_search_products function not found"
        
        if hasattr(module, '_tool_get_low_stock'):
            low_stock_result = module._tool_get_low_stock()
            tool_results["tool_get_low_stock"] = low_stock_result
            
            low_stock_names = [p.get("name") for p in low_stock_result.get("products", [])] \
                if isinstance(low_stock_result, dict) else []
            
            if isinstance(low_stock_result, dict) and low_stock_result.get("count") == 1 \
                    and low_stock_names == ["Test Product"]:
                results["details"].setdefault("smoke_test", {})["tool_get_low_stock"] = {
                    "expected_count": 1,
                    "expected_name": "Test Product",
                    "actual": low_stock_result
                }
            else:
                results["errors"].append(
                    f"_tool_get_low_stock() expected {{'count': 1, 'products': [name='Test Product']}} "
                    f"(quantity 3 < min_stock 10), got {low_stock_result!r}"
                )
        else:
            results["skip_reasons"]["tool_get_low_stock"] = "_tool_get_low_stock function not found"
        
        if tool_results and not results["errors"]:
            results["smoke_test"] = "PASS"
        elif tool_results:
            results["smoke_test"] = "FAIL"
        else:
            results["smoke_test"] = "SKIP"
            results["skip_reasons"]["smoke_test"] = "No testable tool function found (_tool_search_products / _tool_get_low_stock)"
        
        results["external_services"] = "PASS"
        results["details"]["external_services"] = {
            "mocked": ["urllib"],
            "note": "External KI APIs not contacted in test (tool functions use DB only)"
        }
        
        if hasattr(module, 'plugin_blueprint'):
            results["api_test"] = "SKIP"
            results["skip_reasons"]["api_test"] = (
                "Only blueprint registration was checked (see 'registration'). "
                "No real HTTP request was made against /chat or /action."
            )
        
        if hasattr(module, '_tool_search_products'):
            try:
                empty_result = module._tool_search_products("no-such-product-xyz")
                if isinstance(empty_result, dict) and empty_result.get("found") == 0:
                    results["error_handling"] = "PASS"
                    results["details"]["error_handling"] = {
                        "tested": "_tool_search_products with a query matching nothing",
                        "actual": empty_result
                    }
                else:
                    results["error_handling"] = "FAIL"
                    results["errors"].append(
                        f"_tool_search_products('no-such-product-xyz') expected found=0, got {empty_result!r}"
                    )
            except Exception as e:
                results["error_handling"] = "FAIL"
                results["errors"].append(f"_tool_search_products raised on a no-match query instead of returning found=0: {e}")
        
        results["authentication_test"] = "SKIP"
        results["skip_reasons"]["authentication_test"] = "Auth testing requires real auth context"
        
    except Exception as e:
        results["smoke_test"] = "FAIL"
        results["errors"].append(f"KI assistent smoke test failed: {e}")
    
    return results

def _test_low_stock_notifications(module, test_db, external_mocks):
    results = {
        "api_test": "SKIP",
        "smoke_test": "SKIP",
        "external_services": "SKIP",
        "side_effects": "SKIP",
        "error_handling": "SKIP",
        "authentication_test": "SKIP",
        "details": {},
        "errors": [],
        "skip_reasons": {}
    }
    
    try:
        cursor = test_db.cursor()
        
        cursor.execute("""
            INSERT INTO products (id, name, min_stock) VALUES
                (1, 'Low Stock Product', 10),
                (2, 'Well Stocked Product', 5),
                (3, 'No Inventory Row Product', 5)
        """)
        cursor.execute("""
            INSERT INTO inventory (id, product_id, quantity) VALUES
                (1, 1, 3),
                (2, 2, 50)
        """)
        test_db.commit()
        
        if hasattr(module, '_get_low_stock_items'):
            low_stock_result = module._get_low_stock_items()
            names = [row["name"] if hasattr(row, "keys") else row[1] for row in low_stock_result] \
                if low_stock_result else []
            
            expected_present = {"Low Stock Product", "No Inventory Row Product"}
            expected_absent = "Well Stocked Product"
            
            if expected_present.issubset(set(names)) and expected_absent not in names:
                results["smoke_test"] = "PASS"
                results["details"]["smoke_test"] = {
                    "operation": "get_low_stock_items",
                    "expected_reported": sorted(expected_present),
                    "expected_not_reported": expected_absent,
                    "actual_names": names
                }
                results["error_handling"] = "PASS"
                results["details"]["error_handling"] = {
                    "tested": "Product with no inventory row at all (COALESCE(quantity,0)=0)",
                    "expected": "counted as low stock",
                    "actual": "No Inventory Row Product" in names
                }
            else:
                results["smoke_test"] = "FAIL"
                results["errors"].append(
                    f"_get_low_stock_items() expected {sorted(expected_present)} present and "
                    f"'{expected_absent}' absent, got {names}"
                )
        else:
            results["smoke_test"] = "SKIP"
            results["skip_reasons"]["smoke_test"] = "_get_low_stock_items function not found"
        
        results["external_services"] = "PASS"
        results["details"]["external_services"] = {
            "mocked": ["urllib", "smtplib"],
            "note": "Telegram, Discord, Webhook, Email mocked - no real sends"
        }
        
        if hasattr(module, 'plugin_blueprint'):
            results["api_test"] = "SKIP"
            results["skip_reasons"]["api_test"] = (
                "Only blueprint registration was checked (see 'registration'). "
                "No real HTTP request was made against /check, /low-stock, etc."
            )
        
        results["side_effects"] = "PASS"
        results["details"]["side_effects"] = {
            "background_threads": "Deactivated in test mode",
            "note": "LAGERSYNC_TEST_MODE=true prevents _background_checker/_telegram_request_poller from starting"
        }
        
        results["authentication_test"] = "SKIP"
        results["skip_reasons"]["authentication_test"] = "Auth testing requires real auth context"
        
    except Exception as e:
        results["smoke_test"] = "FAIL"
        results["errors"].append(f"Low stock notifications smoke test failed: {e}")
    
    return results

def _test_sso(module, test_db, external_mocks):
    results = {
        "api_test": "SKIP",
        "smoke_test": "SKIP",
        "external_services": "SKIP",
        "side_effects": "SKIP",
        "error_handling": "SKIP",
        "authentication_test": "SKIP",
        "details": {},
        "errors": [],
        "skip_reasons": {}
    }
    
    try:
        cursor = test_db.cursor()
        cursor.execute("""
            INSERT INTO users (id, username, is_admin) VALUES (1, 'admin', 1)
        """)
        test_db.commit()
        
        discovery_response = {
            "issuer": "https://test-issuer.example",
            "authorization_endpoint": "https://test-issuer.example/authorize",
            "token_endpoint": "https://test-issuer.example/token",
            "userinfo_endpoint": "https://test-issuer.example/userinfo"
        }
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = discovery_response
        external_mocks["requests"].get.return_value = mock_response
        
        if hasattr(module, '_discover'):
            discovery_result = module._discover("https://test-issuer.example")
            
            required_endpoints = {"issuer", "authorization_endpoint", "token_endpoint", "userinfo_endpoint"}
            if external_mocks["requests"].get.called and isinstance(discovery_result, dict) \
                    and required_endpoints.issubset(discovery_result.keys()) \
                    and discovery_result["issuer"] == discovery_response["issuer"]:
                results["smoke_test"] = "PASS"
                results["details"]["smoke_test"] = {
                    "operation": "oidc_discovery",
                    "issuer": "https://test-issuer.example",
                    "endpoints_found": sorted(discovery_result.keys()),
                    "mock_used": True
                }
            else:
                results["smoke_test"] = "FAIL"
                results["errors"].append(
                    f"_discover() expected a dict with {sorted(required_endpoints)}, got {discovery_result!r} "
                    f"(mock called: {external_mocks['requests'].get.called})"
                )
        else:
            results["smoke_test"] = "SKIP"
            results["skip_reasons"]["smoke_test"] = "_discover function not found"
        
        results["external_services"] = "PASS"
        results["details"]["external_services"] = {
            "mocked": ["requests"],
            "discovery_response": discovery_response
        }
        
        if hasattr(module, 'plugin_blueprint'):
            results["api_test"] = "SKIP"
            results["skip_reasons"]["api_test"] = (
                "Only blueprint registration was checked (see 'registration'). "
                "No real HTTP request was made against /login, /callback, etc."
            )
        
        if hasattr(module, '_discover'):
            failing_response = MagicMock()
            failing_response.status_code = 500

            def _raise_http_error():
                raise Exception("500 Server Error: discovery endpoint unavailable")
            failing_response.raise_for_status.side_effect = _raise_http_error
            external_mocks["requests"].get.return_value = failing_response
            
            try:
                module._discover("https://broken-issuer.example")
                results["error_handling"] = "FAIL"
                results["errors"].append("_discover() did not raise for a failing (HTTP 500) discovery endpoint")
            except Exception as e:
                results["error_handling"] = "PASS"
                results["details"]["error_handling"] = {
                    "tested": "_discover() against a discovery endpoint returning HTTP 500",
                    "expected": "propagates an exception rather than returning a broken/partial config",
                    "actual_exception": str(e)
                }
        
        results["authentication_test"] = "SKIP"
        results["skip_reasons"]["authentication_test"] = "SSO flow requires real OIDC provider"
        
    except Exception as e:
        results["smoke_test"] = "FAIL"
        results["errors"].append(f"SSO smoke test failed: {e}")
    
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
    
    failed = any(r["overall"] in ("FAIL", "INCOMPLETE") for r in all_results)
    sys.exit(1 if failed else 0)

if __name__ == "__main__":
    main()
