# -*- coding: utf-8 -*-
from flask import Blueprint, request
import urllib.request
import urllib.error
import urllib.parse
import json as json_module
import time

plugin_blueprint = Blueprint("ki_assistent", __name__)

OLLAMA_DEFAULT_URL = "http://localhost:11434"

# ─────────────────────────────────────────────────────────────────────────────
# Tool-Definitionen  (OpenAI-kompatibles Format – funktioniert auch mit Ollama)
# Hinweis: Das Modell muss Tool Calling unterstützen.
#          Empfohlen: llama3.1, llama3.2, mistral-nemo, qwen2.5, phi3.5
# ─────────────────────────────────────────────────────────────────────────────
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_products",
            "description": (
                "Sucht Produkte nach Name, Kurzname oder Barcode. "
                "Gibt Bestand, Lagerort und Mindestbestand zurück. "
                "Nutze dies, wenn der Benutzer nach einem bestimmten Produkt fragt."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Suchbegriff (Produktname, Kurzname oder Barcode)"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximale Anzahl Ergebnisse. Standard: 10, max: 50.",
                        "default": 10
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_low_stock",
            "description": (
                "Gibt alle Produkte zurück, deren aktueller Bestand unter dem "
                "konfigurierten Mindestbestand liegt. "
                "Nutze dies für Fragen zu Nachbestellungen oder kritischen Beständen."
            ),
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_locations",
            "description": "Gibt alle verfügbaren Lagerorte zurück.",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_inventory_by_location",
            "description": "Gibt alle Produkte und deren Bestände an einem bestimmten Lagerort zurück.",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "Exakter Name des Lagerorts (aus get_locations ermitteln)"
                    }
                },
                "required": ["location"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_statistics",
            "description": (
                "Gibt allgemeine Lagerstatistiken zurück: "
                "Gesamtzahl Produkte, Gesamtbestand, Anzahl Produkte unter Mindestbestand, Anzahl Lagerorte."
            ),
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "change_stock",
            "description": (
                "Ändert den Bestand eines Produkts. "
                "Positive delta-Werte buchen ein, negative buchen aus. "
                "NUR nach ausdrücklicher Bestätigung durch den Benutzer aufrufen!"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "product": {
                        "type": "string",
                        "description": "Produktname oder Kurzname"
                    },
                    "delta": {
                        "type": "integer",
                        "description": "Änderungsmenge (positiv = einbuchen, negativ = ausbuchen)"
                    },
                    "location": {
                        "type": "string",
                        "description": "Lagerort (optional, wenn Produkt nur an einem Ort vorkommt)"
                    }
                },
                "required": ["product", "delta"]
            }
        }
    }
]


# ─────────────────────────────────────────────────────────────────────────────
# Hilfsfunktionen
# ─────────────────────────────────────────────────────────────────────────────

def _is_safe_url(url: str, allow_localhost: bool = True) -> bool:
    """Validate URL scheme to prevent SSRF attacks."""
    try:
        parsed = urllib.parse.urlparse(url)
        scheme = (parsed.scheme or '').lower()
        hostname = (parsed.hostname or '').lower()
        if scheme not in ('http', 'https'):
            return False
        if allow_localhost and hostname in ('localhost', '127.0.0.1', '::1'):
            return True
        return scheme == 'https'
    except Exception:
        return False


def _get_ki_settings():
    conn = get_db_connection()
    c = conn.cursor()
    try:
        c.execute("SELECT value FROM settings WHERE key = 'ki_settings'")
        row = c.fetchone()
        if row:
            return json_module.loads(row[0])
    except Exception:
        pass
    finally:
        conn.close()
    return {
        "provider": "ollama",
        "ollama_url": OLLAMA_DEFAULT_URL,
        "ollama_model": "llama3.2",
        "api_url": "",
        "api_key": "",
        "api_model": "gpt-4o-mini",
        "enabled": True,
        "timeout": 600,
        "system_instruction": ""
    }


def _save_ki_settings(settings):
    conn = get_db_connection()
    c = conn.cursor()
    try:
        c.execute(
            "INSERT OR REPLACE INTO settings (key, value) VALUES ('ki_settings', ?)",
            (json_module.dumps(settings),)
        )
        conn.commit()
    finally:
        conn.close()


# ─────────────────────────────────────────────────────────────────────────────
# Tool-Implementierungen  (jede Funktion spricht direkt mit der Datenbank)
# ─────────────────────────────────────────────────────────────────────────────

def _tool_search_products(query: str, limit: int = 10):
    """Sucht Produkte nach Name, Kurzname oder Barcode."""
    try:
        limit = min(max(int(limit), 1), 50)
    except (ValueError, TypeError):
        limit = 10

    conn = get_db_connection()
    c = conn.cursor()
    try:
        c.execute("""
            SELECT p.name, p.short, p.barcode, p.min_stock,
                   COALESCE(i.quantity, 0)   AS stock,
                   COALESCE(l.name, 'Kein Ort') AS location
            FROM products p
            LEFT JOIN inventory i ON p.id = i.product_id
            LEFT JOIN locations l ON i.location = l.name
            WHERE p.name LIKE ? OR p.short LIKE ? OR p.barcode LIKE ?
            ORDER BY p.name
            LIMIT ?
        """, (f"%{query}%", f"%{query}%", f"%{query}%", limit))
        rows = c.fetchall()

        if not rows:
            return {"found": 0, "products": [], "hint": f"Keine Produkte für '{query}' gefunden."}

        products = []
        for name, short, barcode, min_stock, stock, location in rows:
            products.append({
                "name": name,
                "short": short or "",
                "barcode": barcode or "",
                "stock": stock,
                "location": location,
                "min_stock": min_stock or 0,
                "below_min": bool(min_stock and stock < min_stock)
            })

        return {"found": len(products), "products": products}
    finally:
        conn.close()


def _tool_get_low_stock():
    """Gibt alle Produkte zurück, deren Bestand unter dem Mindestbestand liegt."""
    conn = get_db_connection()
    c = conn.cursor()
    try:
        c.execute("""
            SELECT p.name,
                   COALESCE(i.quantity, 0)      AS stock,
                   p.min_stock,
                   COALESCE(l.name, 'Kein Ort') AS location
            FROM products p
            LEFT JOIN inventory i ON p.id = i.product_id
            LEFT JOIN locations l ON i.location = l.name
            WHERE p.min_stock > 0 AND COALESCE(i.quantity, 0) < p.min_stock
            ORDER BY (p.min_stock - COALESCE(i.quantity, 0)) DESC
        """)
        rows = c.fetchall()
        products = [
            {
                "name": r[0],
                "stock": r[1],
                "min_stock": r[2],
                "location": r[3],
                "missing": r[2] - r[1]
            }
            for r in rows
        ]
        return {"count": len(products), "products": products}
    finally:
        conn.close()


def _tool_get_locations():
    """Gibt alle Lagerorte zurück."""
    conn = get_db_connection()
    c = conn.cursor()
    try:
        c.execute("SELECT name FROM locations ORDER BY name")
        locations = [r[0] for r in c.fetchall()]
        return {"locations": locations, "count": len(locations)}
    finally:
        conn.close()


def _tool_get_inventory_by_location(location: str):
    """Gibt das Inventar eines bestimmten Lagerorts zurück."""
    conn = get_db_connection()
    c = conn.cursor()
    try:
        c.execute("""
            SELECT p.name, i.quantity, p.min_stock
            FROM inventory i
            JOIN products p ON p.id = i.product_id
            WHERE i.location = ?
            ORDER BY p.name
        """, (location,))
        rows = c.fetchall()
        products = [{"name": r[0], "stock": r[1], "min_stock": r[2] or 0} for r in rows]
        return {"location": location, "count": len(products), "products": products}
    finally:
        conn.close()


def _tool_get_statistics():
    """Gibt allgemeine Lagerstatistiken zurück."""
    conn = get_db_connection()
    c = conn.cursor()
    try:
        c.execute("SELECT COUNT(*) FROM products")
        total_products = c.fetchone()[0]

        c.execute("SELECT COALESCE(SUM(quantity), 0) FROM inventory")
        total_stock = c.fetchone()[0]

        c.execute("""
            SELECT COUNT(*) FROM products p
            LEFT JOIN inventory i ON p.id = i.product_id
            WHERE p.min_stock > 0 AND COALESCE(i.quantity, 0) < p.min_stock
        """)
        low_stock_count = c.fetchone()[0]

        c.execute("SELECT COUNT(*) FROM locations")
        location_count = c.fetchone()[0]

        return {
            "total_products": total_products,
            "total_stock": total_stock,
            "low_stock_count": low_stock_count,
            "location_count": location_count
        }
    finally:
        conn.close()


def _dispatch_tool(tool_name: str, arguments: dict):
    """Führt einen Tool-Aufruf aus und gibt das Ergebnis zurück."""
    try:
        if tool_name == "search_products":
            return _tool_search_products(
                arguments.get("query", ""),
                arguments.get("limit", 10)
            )
        elif tool_name == "get_low_stock":
            return _tool_get_low_stock()
        elif tool_name == "get_locations":
            return _tool_get_locations()
        elif tool_name == "get_inventory_by_location":
            return _tool_get_inventory_by_location(arguments.get("location", ""))
        elif tool_name == "get_statistics":
            return _tool_get_statistics()
        elif tool_name == "change_stock":
            result, error = _execute_action("change_stock", arguments)
            if error:
                return {"error": error}
            return {"success": True, "message": result}
        else:
            return {"error": f"Unbekanntes Tool: {tool_name}"}
    except Exception as e:
        return {"error": f"Tool-Fehler bei '{tool_name}': {str(e)}"}


# ─────────────────────────────────────────────────────────────────────────────
# KI-Aufrufe mit Tool-Support
# Beide Provider (Ollama + OpenAI) geben ein einheitliches Result-Dict zurück:
#   {"type": "text",       "content": "..."}   → KI hat geantwortet
#   {"type": "tool_calls", "content": "...",
#    "tool_calls": [...]}                       → KI will Tools aufrufen
# ─────────────────────────────────────────────────────────────────────────────

def _call_ollama(settings, messages):
    """Ruft Ollama mit Tool-Support auf."""
    url = settings.get("ollama_url", OLLAMA_DEFAULT_URL) + "/api/chat"
    model = settings.get("ollama_model", "llama3.2")

    if not _is_safe_url(url, allow_localhost=True):
        return None, "URL scheme not allowed"

    payload = {"model": model, "messages": messages, "tools": TOOLS, "stream": False}

    req = urllib.request.Request(
        url,
        data=json_module.dumps(payload).encode('utf-8'),
        headers={"Content-Type": "application/json"}
    )

    timeout = settings.get("timeout", 120)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:  # nosec B310
            data = json_module.loads(resp.read().decode('utf-8'))
            message = data.get("message", {})
            tool_calls_raw = message.get("tool_calls") or []

            if tool_calls_raw:
                # Ollama-Format normalisieren: kein 'id', Argumente bereits als dict
                tool_calls = []
                for i, tc in enumerate(tool_calls_raw):
                    fn = tc.get("function", {})
                    tool_calls.append({
                        "id": f"ollama_{int(time.time() * 1000)}_{i}",
                        "type": "function",
                        "function": {
                            "name": fn.get("name", ""),
                            "arguments": fn.get("arguments", {})  # schon dict bei Ollama
                        }
                    })
                return {
                    "type": "tool_calls",
                    "content": message.get("content") or "",
                    "tool_calls": tool_calls
                }, None

            return {"type": "text", "content": message.get("content", "")}, None

    except urllib.error.HTTPError as e:
        body = e.read().decode('utf-8') if e.fp else ""
        return None, f"Ollama HTTP {e.code}: {body[:200]}"
    except urllib.error.URLError as e:
        return None, f"Ollama nicht erreichbar: {e.reason}"
    except Exception as e:
        return None, str(e)


def _call_openai(settings, messages):
    """Ruft eine OpenAI-kompatible API mit Tool-Support auf."""
    url = settings.get("api_url", "https://api.openai.com/v1/chat/completions")
    api_key = settings.get("api_key", "")
    model = settings.get("api_model", "gpt-4o-mini")

    if not api_key:
        return None, "API-Key nicht konfiguriert"
    if not _is_safe_url(url, allow_localhost=False):
        return None, "URL scheme not allowed (HTTPS required)"

    payload = {"model": model, "messages": messages, "tools": TOOLS, "max_tokens": 1000}

    req = urllib.request.Request(
        url,
        data=json_module.dumps(payload).encode('utf-8'),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
    )

    timeout = settings.get("timeout", 120)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:  # nosec B310
            data = json_module.loads(resp.read().decode('utf-8'))
            choice = data.get("choices", [{}])[0]
            message = choice.get("message", {})
            finish_reason = choice.get("finish_reason", "")

            if finish_reason == "tool_calls" or message.get("tool_calls"):
                tool_calls = []
                for tc in message.get("tool_calls", []):
                    fn = tc.get("function", {})
                    args_raw = fn.get("arguments", "{}")
                    try:
                        args = json_module.loads(args_raw) if isinstance(args_raw, str) else args_raw
                    except Exception:
                        args = {}
                    tool_calls.append({
                        "id": tc.get("id", f"call_{int(time.time() * 1000)}"),
                        "type": "function",
                        "function": {"name": fn.get("name", ""), "arguments": args}
                    })
                return {
                    "type": "tool_calls",
                    "content": message.get("content") or "",
                    "tool_calls": tool_calls
                }, None

            return {"type": "text", "content": message.get("content", "")}, None

    except urllib.error.HTTPError as e:
        body = e.read().decode('utf-8') if e.fp else ""
        return None, f"API-Fehler {e.code}: {body[:200]}"
    except Exception as e:
        return None, str(e)


# ─────────────────────────────────────────────────────────────────────────────
# Agentischer Chat-Loop
# ─────────────────────────────────────────────────────────────────────────────

def _agentic_chat(settings, messages):  # NOSONAR – gewollte Komplexität
    """
    Führt den agentic Loop aus:
      1. Nachricht an KI schicken
      2. KI ruft Tools auf  → ausführen → Ergebnis zurückschicken
      3. Wiederholen, bis KI eine reine Textantwort gibt
    Gibt zurück: (response_text, error, tools_used_list)
    """
    provider = settings.get("provider", "ollama")
    tools_used = []
    MAX_ITERATIONS = 10  # Schutz gegen Endlosschleife

    for _ in range(MAX_ITERATIONS):
        if provider == "ollama":
            result, error = _call_ollama(settings, messages)
        else:
            result, error = _call_openai(settings, messages)

        if error:
            return None, error, tools_used

        # KI hat eine Textantwort geliefert → fertig
        if result["type"] == "text":
            return result["content"], None, tools_used

        # KI will Tools aufrufen
        if result["type"] == "tool_calls":
            # Assistenten-Nachricht mit Tool-Calls zur History hinzufügen
            messages.append({
                "role": "assistant",
                "content": result.get("content") or "",
                "tool_calls": result["tool_calls"]
            })

            # Jedes Tool ausführen und Ergebnis an History anhängen
            for tc in result["tool_calls"]:
                tool_name = tc["function"]["name"]
                arguments = tc["function"]["arguments"]

                # Argumente sicherstellen: müssen dict sein
                if not isinstance(arguments, dict):
                    try:
                        arguments = json_module.loads(str(arguments))
                    except Exception:
                        arguments = {}

                tool_result = _dispatch_tool(tool_name, arguments)
                tools_used.append(tool_name)

                messages.append({
                    "role": "tool",
                    "tool_call_id": tc["id"],
                    "content": json_module.dumps(tool_result, ensure_ascii=False)
                })

    return None, f"Abbruch nach {MAX_ITERATIONS} Tool-Aufrufen ohne Textantwort", tools_used


# ─────────────────────────────────────────────────────────────────────────────
# Bestandsänderung (unverändert vom Original)
# ─────────────────────────────────────────────────────────────────────────────

def _update_inventory_stock(c, prod_id, location, delta):
    timestamp = int(time.time() * 1000)
    if location:
        c.execute("SELECT quantity FROM inventory WHERE product_id = ? AND location = ?",
                  (prod_id, location))
        inv_row = c.fetchone()
        old_stock = inv_row[0] if inv_row else 0
        new_stock = old_stock + delta
        if inv_row:
            c.execute(
                "UPDATE inventory SET quantity = ?, last_changed = ? WHERE product_id = ? AND location = ?",
                (new_stock, timestamp, prod_id, location)
            )
        else:
            c.execute(
                "INSERT INTO inventory (location, product_id, quantity, last_changed) VALUES (?, ?, ?, ?)",
                (location, prod_id, new_stock, timestamp)
            )
    else:
        c.execute("SELECT location, quantity FROM inventory WHERE product_id = ?", (prod_id,))
        inv_rows = c.fetchall()
        if inv_rows:
            loc, old_stock = inv_rows[0]
            new_stock = old_stock + delta
            c.execute(
                "UPDATE inventory SET quantity = ?, last_changed = ? WHERE product_id = ? AND location = ?",
                (new_stock, timestamp, prod_id, loc)
            )
        else:
            return None, "Kein Lagerort für Produkt gefunden. Bitte Ort angeben."
    return old_stock, new_stock


def _execute_action(action, params):
    conn = get_db_connection()
    c = conn.cursor()
    try:
        if action == "change_stock":
            product_name = params.get("product", "")
            location = params.get("location", None)
            delta = int(params.get("delta", 0))

            c.execute(
                "SELECT id, name FROM products WHERE name LIKE ? OR short LIKE ?",
                (f"%{product_name}%", f"%{product_name}%")
            )
            row = c.fetchone()
            if not row:
                return None, f"Produkt '{product_name}' nicht gefunden"

            prod_id, real_name = row
            stock_result = _update_inventory_stock(c, prod_id, location, delta)
            if isinstance(stock_result, tuple) and stock_result[0] is None:
                return stock_result

            old_stock, new_stock = stock_result
            c.execute(
                "INSERT INTO inventory_events (product_id, delta, new_qty, user, timestamp) VALUES (?, ?, ?, ?, ?)",
                (prod_id, delta, new_stock, "KI-Assistent", str(int(time.time() * 1000)))
            )
            conn.commit()
            sign = "+" if delta > 0 else ""
            return f"✅ Bestand von '{real_name}' geändert: {old_stock} → {new_stock} ({sign}{delta})", None

        return None, "Unbekannte Aktion"
    except Exception as e:
        return None, str(e)
    finally:
        conn.close()


# ─────────────────────────────────────────────────────────────────────────────
# Routen
# ─────────────────────────────────────────────────────────────────────────────

@plugin_blueprint.route("/settings", methods=["GET"])
@require_auth()
def get_settings():
    settings = _get_ki_settings()
    if settings.get("api_key"):
        settings["api_key_masked"] = settings["api_key"][:8] + "..." + settings["api_key"][-4:]
        settings["api_key"] = ""
    return json_response({"status": "ok", "settings": settings})


@plugin_blueprint.route("/settings", methods=["POST"])
@require_auth()
def save_settings():
    data = request.json or {}
    current = _get_ki_settings()

    allowed_keys = ["provider", "ollama_url", "ollama_model", "api_url", "api_key",
                    "api_model", "enabled", "timeout", "system_instruction"]
    for key in allowed_keys:
        if key in data:
            if key == "api_key" and data[key] == "********":
                continue
            current[key] = data[key]

    _save_ki_settings(current)
    return json_response({"status": "ok"})


@plugin_blueprint.route("/test", methods=["POST"])
@require_auth()
def test_connection():
    settings = request.json or {}
    provider = settings.get("provider", "ollama")

    # Einfacher Test ohne Tools
    test_msg = [{"role": "user", "content": "Antworte nur mit dem Wort OK."}]
    payload_no_tools = {"model": settings.get("ollama_model" if provider == "ollama" else "api_model"),
                        "messages": test_msg, "stream": False}

    if provider == "ollama":
        url = settings.get("ollama_url", OLLAMA_DEFAULT_URL) + "/api/chat"
        if not _is_safe_url(url, allow_localhost=True):
            return json_response({"status": "error", "message": "Ungültige URL"})
        req = urllib.request.Request(
            url,
            data=json_module.dumps(payload_no_tools).encode('utf-8'),
            headers={"Content-Type": "application/json"}
        )
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:  # nosec B310
                data = json_module.loads(resp.read().decode('utf-8'))
                content = data.get("message", {}).get("content", "OK")
                return json_response({"status": "ok", "response": content[:100]})
        except Exception as e:
            return json_response({"status": "error", "message": str(e)})
    else:
        api_key = settings.get("api_key", "")
        url = settings.get("api_url", "https://api.openai.com/v1/chat/completions")
        if not api_key:
            return json_response({"status": "error", "message": "API-Key fehlt"})
        if not _is_safe_url(url, allow_localhost=False):
            return json_response({"status": "error", "message": "Ungültige URL"})
        payload_no_tools["model"] = settings.get("api_model", "gpt-4o-mini")
        req = urllib.request.Request(
            url,
            data=json_module.dumps(payload_no_tools).encode('utf-8'),
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}
        )
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:  # nosec B310
                data = json_module.loads(resp.read().decode('utf-8'))
                content = data.get("choices", [{}])[0].get("message", {}).get("content", "OK")
                return json_response({"status": "ok", "response": content[:100]})
        except Exception as e:
            return json_response({"status": "error", "message": str(e)})


@plugin_blueprint.route("/models", methods=["GET"])
@require_auth()
def list_models():
    settings = _get_ki_settings()
    if settings.get("provider") != "ollama":
        return json_response({"status": "ok", "models": [], "note": "Nur für Ollama verfügbar"})

    url = settings.get("ollama_url", OLLAMA_DEFAULT_URL) + "/api/tags"
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=10) as resp:  # nosec B310
            data = json_module.loads(resp.read().decode('utf-8'))
            models = [m.get("name", "") for m in data.get("models", [])]
            return json_response({"status": "ok", "models": models})
    except Exception as e:
        return json_response({"status": "error", "message": str(e), "models": []})


@plugin_blueprint.route("/chat", methods=["POST"])
@require_auth()
def chat():  # NOSONAR – KI-Chat mit agentic Loop
    data = request.json or {}
    user_message = data.get("message", "")
    history = data.get("history", [])

    if not user_message:
        return json_response({"status": "error", "message": "Keine Nachricht"})

    settings = _get_ki_settings()
    if not settings.get("enabled", True):
        return json_response({"status": "error", "message": "KI-Assistent deaktiviert"})

    user_instruction = settings.get("system_instruction", "").strip()
    system_prompt = (
        "Du bist ein intelligenter Lagerassistent mit direktem Zugriff auf das Warenlager-System.\n\n"
        "Du verfügst über folgende Werkzeuge:\n"
        "• search_products – Produkte nach Name/Kurzname/Barcode suchen\n"
        "• get_low_stock – Alle Produkte unter Mindestbestand abrufen\n"
        "• get_locations – Alle Lagerorte anzeigen\n"
        "• get_inventory_by_location – Inventar eines Lagerorts abfragen\n"
        "• get_statistics – Allgemeine Lagerstatistiken abrufen\n"
        "• change_stock – Bestand ändern (NUR nach ausdrücklicher Bestätigung!)\n\n"
        "Nutze die Werkzeuge aktiv, statt zu raten. "
        "Antworte präzise in der Sprache des Benutzers."
    )
    if user_instruction:
        system_prompt += f"\n\nZwingende Anweisung (höchste Priorität): {user_instruction}"

    messages = [{"role": "system", "content": system_prompt}]

    # Chat-History bereinigen und anhängen (max. letzte 20 Nachrichten)
    if isinstance(history, list):
        for item in history[-20:]:
            if not isinstance(item, dict):
                continue
            role = item.get("role")
            content = item.get("content")
            if role not in ("user", "assistant") or content is None:
                continue
            messages.append({"role": role, "content": str(content)})

    messages.append({"role": "user", "content": user_message})

    response, error, tools_used = _agentic_chat(settings, messages)

    if error:
        return json_response({"status": "error", "message": error})

    return json_response({
        "status": "ok",
        "response": response,
        "tools_used": tools_used
    })


@plugin_blueprint.route("/action", methods=["POST"])
@require_auth()
def execute_action():
    data = request.json or {}
    action = data.get("action", "")
    params = data.get("params", {})
    result, error = _execute_action(action, params)
    if error:
        return json_response({"status": "error", "message": error})
    return json_response({"status": "ok", "result": result})
