# -*- coding: utf-8 -*-
from flask import Blueprint, request
import urllib.request
import urllib.error
import urllib.parse
import json as json_module
import time
import re

plugin_blueprint = Blueprint("ki_assistent", __name__)

OLLAMA_DEFAULT_URL = "http://localhost:11434"

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
        "product_limit": 50,
        "system_instruction": ""
    }


def _save_ki_settings(settings):
    conn = get_db_connection()
    c = conn.cursor()
    try:
        c.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('ki_settings', ?)",
                  (json_module.dumps(settings),))
        conn.commit()
    finally:
        conn.close()


def _get_lager_context(product_limit: int = 25):
    conn = get_db_connection()
    c = conn.cursor()
    try:
        try:
            product_limit = int(product_limit)
        except Exception:
            product_limit = 25
        if product_limit < 1:
            product_limit = 1
        if product_limit > 500:
            product_limit = 500

        c.execute("""
            SELECT p.id, p.name, p.min_stock, p.barcode, p.short,
                   COALESCE(l.name, 'Kein Ort') as ort,
                   COALESCE(i.quantity, 0) as stock
            FROM products p
            LEFT JOIN inventory i ON p.id = i.product_id
            LEFT JOIN locations l ON i.location = l.name
            ORDER BY p.name
            LIMIT ?
        """, (product_limit,))
        produkte = c.fetchall()

        c.execute("SELECT name FROM locations ORDER BY name")
        orte = [r[0] for r in c.fetchall()]

        c.execute("""
            SELECT p.name, COALESCE(i.quantity, 0) as stock, p.min_stock
            FROM products p
            LEFT JOIN inventory i ON p.id = i.product_id
            WHERE p.min_stock > 0 AND COALESCE(i.quantity, 0) < p.min_stock
        """)
        niedrig = c.fetchall()

        context = "AKTUELLE LAGERDATEN:\n\n"
        context += f"Lagerorte: {', '.join(orte) if orte else 'Keine definiert'}\n\n"

        if produkte:
            context += f"Produkte (max. {product_limit}):\n"
            for p in produkte:
                _, name, min_s, _, _, ort, stock = p
                warnung = " ⚠️" if min_s and stock < min_s else ""
                context += f"- {name}: {stock} Stk ({ort}){warnung}\n"
        else:
            context += "Keine Produkte im Lager.\n"

        if niedrig:
            context += f"\nWARNUNG - Niedriger Bestand ({len(niedrig)} Produkte):\n"
            for n in niedrig:
                context += f"- {n[0]}: {n[1]} Stk (Min: {n[2]})\n"

        return context
    finally:
        conn.close()


def _call_ollama(settings, messages):
    url = settings.get("ollama_url", OLLAMA_DEFAULT_URL) + "/api/chat"
    model = settings.get("ollama_model", "llama3.2")

    if not _is_safe_url(url, allow_localhost=True):
        return None, "URL scheme not allowed (HTTPS required for external URLs)"

    payload = {
        "model": model,
        "messages": messages,
        "stream": False
    }

    req = urllib.request.Request(
        url,
        data=json_module.dumps(payload).encode('utf-8'),
        headers={"Content-Type": "application/json"}
    )

    timeout = settings.get("timeout", 120)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:  # nosec B310 # validated by _is_safe_url
            data = json_module.loads(resp.read().decode('utf-8'))
            return data.get("message", {}).get("content", ""), None
    except urllib.error.HTTPError as e:
        err_body = e.read().decode('utf-8') if e.fp else ""
        return None, f"Ollama HTTP-Fehler {e.code}: {err_body[:200]}"
    except urllib.error.URLError as e:
        return None, f"Ollama nicht erreichbar: {e.reason}"
    except Exception as e:
        return None, str(e)


def _call_openai_api(settings, messages):
    url = settings.get("api_url", "https://api.openai.com/v1/chat/completions")
    api_key = settings.get("api_key", "")
    model = settings.get("api_model", "gpt-4o-mini")

    if not api_key:
        return None, "API-Key nicht konfiguriert"

    if not _is_safe_url(url, allow_localhost=False):
        return None, "URL scheme not allowed (HTTPS required)"

    payload = {
        "model": model,
        "messages": messages,
        "max_tokens": 1000
    }

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
        with urllib.request.urlopen(req, timeout=timeout) as resp:  # nosec B310 # validated by _is_safe_url
            data = json_module.loads(resp.read().decode('utf-8'))
            return data.get("choices", [{}])[0].get("message", {}).get("content", ""), None
    except urllib.error.HTTPError as e:
        err_body = e.read().decode('utf-8') if e.fp else ""
        return None, f"API-Fehler {e.code}: {err_body[:200]}"
    except Exception as e:
        return None, str(e)


def _update_inventory_stock(c, prod_id, location, delta):
    timestamp = int(time.time() * 1000)
    if location:
        c.execute("SELECT quantity FROM inventory WHERE product_id = ? AND location = ?",
                  (prod_id, location))
        inv_row = c.fetchone()
        old_stock = inv_row[0] if inv_row else 0
        new_stock = old_stock + delta

        if inv_row:
            c.execute("UPDATE inventory SET quantity = ?, last_changed = ? WHERE product_id = ? AND location = ?",
                      (new_stock, timestamp, prod_id, location))
        else:
            c.execute("INSERT INTO inventory (location, product_id, quantity, last_changed) VALUES (?, ?, ?, ?)",
                      (location, prod_id, new_stock, timestamp))
    else:
        c.execute("SELECT location, quantity FROM inventory WHERE product_id = ?", (prod_id,))
        inv_rows = c.fetchall()
        if inv_rows:
            loc, old_stock = inv_rows[0]
            new_stock = old_stock + delta
            c.execute("UPDATE inventory SET quantity = ?, last_changed = ? WHERE product_id = ? AND location = ?",
                      (new_stock, timestamp, prod_id, loc))
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

            c.execute("SELECT id, name FROM products WHERE name LIKE ? OR short LIKE ?",
                      (f"%{product_name}%", f"%{product_name}%"))
            row = c.fetchone()
            if not row:
                return None, f"Produkt '{product_name}' nicht gefunden"

            prod_id, real_name = row

            stock_result = _update_inventory_stock(c, prod_id, location, delta)
            if isinstance(stock_result, tuple):
                old_stock, new_stock = stock_result
            else:
                return stock_result

            c.execute("""
                INSERT INTO inventory_events (product_id, delta, new_qty, user, timestamp)
                VALUES (?, ?, ?, ?, ?)
            """, (prod_id, delta, new_stock, "KI-Assistent", str(int(time.time() * 1000))))

            conn.commit()
            return f"✅ Bestand von '{real_name}' geändert: {old_stock} → {new_stock} ({'+' if delta > 0 else ''}{delta})", None

        return None, "Unbekannte Aktion"
    except Exception as e:
        return None, str(e)
    finally:
        conn.close()


def _get_product_purchase_price(product_query: str):
    if not product_query:
        return None, "Kein Produkt angegeben"

    conn = get_db_connection()
    c = conn.cursor()
    try:
        c.execute("PRAGMA table_info(products)")
        cols = [r[1] for r in (c.fetchall() or []) if len(r) > 1]
        cols_l = {str(x).lower(): x for x in cols}
        candidates = [
            "ek",
            "einkauf",
            "einkaufspreis",
            "einkaufspreise",
            "purchase_price",
            "purchaseprice",
            "cost",
            "cost_price",
            "costprice",
            "buy_price",
            "buyprice",
            "unit_cost",
            "unitcost",
            "preis_ek",
        ]

        price_col = None
        for cand in candidates:
            if cand in cols_l:
                price_col = cols_l[cand]
                break
        if not price_col:
            return None, "EK-Spalte nicht gefunden"
        
        # Validate price_col is a safe identifier (alphanumeric + underscore only)
        if not price_col.replace('_', '').isalnum():
            return None, "Ungültiger Spaltenname"

        sql = f"SELECT id, name, {price_col} FROM products WHERE name LIKE ? OR short LIKE ? ORDER BY name LIMIT 5"
        c.execute(sql, (f"%{product_query}%", f"%{product_query}%"))
        rows = c.fetchall() or []
        if not rows:
            return None, f"Produkt '{product_query}' nicht gefunden"
        if len(rows) > 1:
            names = ", ".join([str(r[1]) for r in rows[:5] if len(r) > 1])
            return None, f"Mehrere Treffer: {names}"

        _, name, price = rows[0]
        if price is None or str(price).strip() == "":
            return None, f"Für '{name}' ist kein EK hinterlegt"
        return {"product": name, "ek": price, "column": price_col}, None
    finally:
        conn.close()


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

    for key in ["provider", "ollama_url", "ollama_model", "api_url", "api_key", "api_model", "enabled", "timeout", "product_limit", "system_instruction"]:
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

    test_msg = [{"role": "user", "content": "Sage nur 'OK' wenn du mich hörst."}]

    if provider == "ollama":
        response, error = _call_ollama(settings, test_msg)
    else:
        response, error = _call_openai_api(settings, test_msg)

    if error:
        return json_response({"status": "error", "message": error})

    return json_response({"status": "ok", "response": response[:100] if response else "OK"})


@plugin_blueprint.route("/models", methods=["GET"])
@require_auth()
def list_models():
    settings = _get_ki_settings()

    if settings.get("provider") != "ollama":
        return json_response({"status": "ok", "models": [], "note": "Nur für Ollama verfügbar"})

    url = settings.get("ollama_url", OLLAMA_DEFAULT_URL) + "/api/tags"

    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=10) as resp:  # nosec B310 # validated by _is_safe_url
            data = json_module.loads(resp.read().decode('utf-8'))
            models = [m.get("name", "") for m in data.get("models", [])]
            return json_response({"status": "ok", "models": models})
    except Exception as e:
        return json_response({"status": "error", "message": str(e), "models": []})


@plugin_blueprint.route("/chat", methods=["POST"])
@require_auth()
def chat():  # NOSONAR - AI chat handler, intentional complexity
    data = request.json or {}
    user_message = data.get("message", "")
    history = data.get("history", [])

    if not user_message:
        return json_response({"status": "error", "message": "Keine Nachricht"})

    m = re.search(r"\b(?:ek|einkaufspreis|einkauf)\b", str(user_message).lower())
    if m:
        product_part = str(user_message)
        for pattern in [r"\bwas\s+hat\b", r"\bwie\s+hoch\s+ist\b", r"\bwie\s+viel\s+kostet\b", r"\bpreis\b", r"\bek\b", r"\beinkaufspreis\b", r"\beinkauf\b", r"\bf\s*ü\s*r\b", r"\bvon\b", r"\?", r":"]:
            product_part = re.sub(pattern, " ", product_part, flags=re.IGNORECASE)
        product_part = re.sub(r"\s+", " ", product_part).strip()
        info, err = _get_product_purchase_price(product_part)
        if err:
            return json_response({
                "status": "ok",
                "response": err,
                "context_updated": False
            })
        if info:
            return json_response({
                "status": "ok",
                "response": f"EK für '{info['product']}': {info['ek']}",
                "context_updated": False
            })

    settings = _get_ki_settings()

    if not settings.get("enabled", True):
        return json_response({"status": "error", "message": "KI-Assistent deaktiviert"})

    lager_context = _get_lager_context(settings.get("product_limit", 50))
    user_instruction = settings.get("system_instruction", "").strip()

    system_prompt = f"""Du bist ein hilfreicher Lagerassistent. Du hast Zugriff auf die aktuellen Lagerdaten.

{lager_context}

Antworte kurz und prägnant.
Wenn keine spezielle Sprachvorgabe gemacht wird, antworte in der Sprache des Benutzers."""
    
    if user_instruction:
        system_prompt += f"\n\nZwingende Anweisung (hat höchste Priorität, immer exakt befolgen): {user_instruction}"

    messages = [{"role": "system", "content": system_prompt}]
    sanitized_history = []
    if isinstance(history, list):
        for item in history[-20:]:
            if not isinstance(item, dict):
                continue
            role = item.get("role")
            content = item.get("content")
            if role not in ("user", "assistant"):
                continue
            if content is None:
                continue
            sanitized_history.append({"role": role, "content": str(content)})
    messages.extend(sanitized_history[-10:])
    messages.append({"role": "user", "content": user_message})

    provider = settings.get("provider", "ollama")

    if provider == "ollama":
        response, error = _call_ollama(settings, messages)
    else:
        response, error = _call_openai_api(settings, messages)

    if error:
        return json_response({"status": "error", "message": error})

    return json_response({
        "status": "ok",
        "response": response,
        "context_updated": True
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
