from flask import Blueprint, request
import urllib.request
import urllib.error
import urllib.parse
import json as json_module
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import threading
import time as time_module
import os

# Config key constants (S1192)
_KEY_TG_TOKEN = "telegram_token"
_KEY_TG_CHAT = "telegram_chat_id"
_KEY_TG_PENDING = "telegram_pending"
_KEY_EMAIL_PASS = "email_password"
_ENC_UTF8 = "utf-8"
_MASKED = "********"
_CONTENT_TYPE_JSON = "application/json"


_threads_started = False

plugin_blueprint = Blueprint("low_stock_notifications", __name__)

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

def _default_notify_settings():
    return {
        "enabled": True,
        "check_interval": 60,
        "notify_username_filter": "",
        "telegram_enabled": False,
        _KEY_TG_TOKEN: "",
        _KEY_TG_CHAT: "",
        "telegram_requests_enabled": True,
        _KEY_TG_PENDING: [],
        "notify_login": True,
        "notify_ip_change": True,
        "notify_new_trusted_device": True,
        "notify_new_trusted_device_manual": True,
        "notify_pin_change": True,
        "notify_stock_change": True,
        "notify_low_stock": True,
        "discord_enabled": False,
        "discord_webhook": "",
        "webhook_enabled": False,
        "webhook_url": "",
        "email_enabled": False,
        "email_smtp": "",
        "email_port": 587,
        "email_user": "",
        _KEY_EMAIL_PASS: "",
        "email_to": "",
        "email_use_tls": True,
        "last_low_stock": [],
        "last_allowed_ips": [],
        "last_sessions": []
    }

def _get_notify_settings():
    conn = get_db_connection()
    c = conn.cursor()
    try:
        c.execute("SELECT value FROM settings WHERE key = 'notify_settings'")
        row = c.fetchone()
        if row:
            try:
                loaded = json_module.loads(row[0])
            except Exception:
                loaded = None
            base = _default_notify_settings()
            if isinstance(loaded, dict):
                base.update(loaded)
            if not isinstance(base.get('last_low_stock'), list):
                base['last_low_stock'] = []
            if not isinstance(base.get('last_allowed_ips'), list):
                base['last_allowed_ips'] = []
            if not isinstance(base.get('last_sessions'), list):
                base['last_sessions'] = []
            return base
    except Exception:
        pass
    finally:
        conn.close()


def _is_entry_disabled(entry, pid):
    if isinstance(entry, dict) and entry.get('enabled') is False:
        return True
    if entry is False:
        return True
    if isinstance(entry, dict) and (entry.get('id') == pid or entry.get('name') == pid):
        if entry.get('enabled') is False:
            return True
    return False


def _check_pid_disabled_in_settings_obj(pid: str, obj) -> bool:
    """Check if plugin is explicitly disabled in a parsed settings object. Returns True if disabled."""
    try:
        if isinstance(obj, dict):
            if pid in obj:
                if _is_entry_disabled(obj.get(pid), pid):
                    return True
            for vv in obj.values():
                if _is_entry_disabled(vv, pid):
                    return True
        elif isinstance(obj, list):
            for it in obj:
                if _is_entry_disabled(it, pid):
                    return True
    except Exception:
        pass
    return False


def _check_plugin_in_db_settings(pid):
    conn = get_db_connection()
    c = conn.cursor()
    try:
        try:
            c.execute("SELECT key, value FROM settings WHERE key LIKE '%plugin%' OR key LIKE '%Plugin%' OR key LIKE '%plugins%' OR key LIKE '%Plugins%'")
            rows = c.fetchall() or []
        except Exception:
            rows = []
        for r in rows:
            try:
                v = r[1] if isinstance(r, (list, tuple)) else r['value']
            except Exception:
                continue
            if not v:
                continue
            try:
                obj = json_module.loads(v)
            except Exception:
                continue
            if _check_pid_disabled_in_settings_obj(pid, obj):
                return False
    finally:
        try:
            conn.close()
        except Exception:
            pass
    return None


def _check_plugin_meta_file():
    try:
        base_dir = os.path.dirname(__file__)
        meta_path = os.path.join(base_dir, 'plugin.json')
        if os.path.exists(meta_path):
            with open(meta_path, 'r', encoding=_ENC_UTF8) as f:
                meta = json_module.load(f)
            if isinstance(meta, dict) and meta.get('enabled') is False:
                return False
    except Exception:
        pass
    return None


def _is_plugin_manager_enabled(plugin_id: str) -> bool:
    """Best-effort check if the plugin is enabled in the host's plugin manager.
    If we cannot determine state, assume enabled to avoid breaking functionality.
    """
    pid = str(plugin_id or '').strip()
    if not pid:
        return True
    
    db_result = _check_plugin_in_db_settings(pid)
    if db_result is False:
        return False
    
    meta_result = _check_plugin_meta_file()
    if meta_result is False:
        return False
    
    return True


def _save_notify_settings(settings):
    conn = get_db_connection()
    c = conn.cursor()
    try:
        c.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('notify_settings', ?)",
                  (json_module.dumps(settings),))
        conn.commit()
    finally:
        conn.close()


@plugin_blueprint.route("/users", methods=["GET"])
@require_auth()
def get_users():
    conn = get_db_connection()
    c = conn.cursor()
    try:
        try:
            c.execute("SELECT username FROM users ORDER BY username ASC")
            rows = c.fetchall() or []
        except Exception:
            rows = []
        users = []
        for r in rows:
            try:
                u = r[0] if isinstance(r, (list, tuple)) else r.get('username')
            except Exception:
                u = None
            u = str(u or '').strip()
            if u:
                users.append(u)
        return json_response({"status": "ok", "users": users})
    finally:
        conn.close()


def _mask_secret(value: str):
    try:
        s = str(value or "")
        if not s:
            return ""
        if len(s) <= 8:
            return _MASKED
        return s[:6] + "..." + s[-4:]
    except Exception:
        return ""


def _is_masked_secret(value: str) -> bool:
    try:
        s = str(value or "")
        if not s:
            return True
        if s == _MASKED:
            return True
        if "..." in s:
            return True
        return False
    except Exception:
        return True

def _send_telegram(settings, message):
    token = settings.get(_KEY_TG_TOKEN, "")
    chat_id = settings.get(_KEY_TG_CHAT, "")
    if not token or not chat_id:
        return False, "Telegram nicht konfiguriert (Token oder Chat-ID fehlt)"

    if not token.replace('_', '').replace('-', '').replace(':', '').isalnum():
        return False, "Telegram Token Format ungültig"
    url = f"https://api.telegram.org/bot{token}/sendMessage"  # NOSONAR
    if not _is_safe_url(url, allow_localhost=False):
        return False, "Telegram URL ungültig"
    payload = {"chat_id": chat_id, "text": message, "parse_mode": "HTML"}

    try:
        req = urllib.request.Request(
            url,
            data=json_module.dumps(payload).encode(_ENC_UTF8),
            headers={"Content-Type": _CONTENT_TYPE_JSON}
        )
        with urllib.request.urlopen(req, timeout=15) as _:  # nosec B310 # NOSONAR
            data = json_module.loads(_.read().decode(_ENC_UTF8))
            if data.get("ok"):
                return True, None
            return False, f"Telegram API-Fehler: {data.get('description', 'Unbekannt')}"
    except urllib.error.HTTPError as e:
        err_body = e.read().decode(_ENC_UTF8) if e.fp else ""
        try:
            err_json = json_module.loads(err_body)
            err_msg = err_json.get("description", err_body[:100])
        except json_module.JSONDecodeError:
            err_msg = err_body[:100] if err_body else f"HTTP {e.code}"
        return False, f"Telegram HTTP {e.code}: {err_msg}"
    except urllib.error.URLError as e:
        return False, f"Telegram nicht erreichbar: {e.reason}"
    except Exception as e:
        return False, str(e)


def _send_discord(settings, message):
    webhook_url = settings.get("discord_webhook", "")
    if not webhook_url:
        return False, "Discord Webhook nicht konfiguriert"

    if not _is_safe_url(webhook_url, allow_localhost=False):
        return False, "Discord Webhook URL muss HTTPS verwenden"

    payload = {"content": message}

    try:
        req = urllib.request.Request(
            webhook_url,  # NOSONAR - validated by _is_safe_url
            data=json_module.dumps(payload).encode(_ENC_UTF8),
            headers={"Content-Type": _CONTENT_TYPE_JSON}
        )
        with urllib.request.urlopen(req, timeout=15) as _:  # nosec B310 # NOSONAR
            return True, None
    except urllib.error.HTTPError as e:
        err_body = e.read().decode(_ENC_UTF8) if e.fp else ""
        return False, f"Discord HTTP {e.code}: {err_body[:100]}"
    except urllib.error.URLError as e:
        return False, f"Discord nicht erreichbar: {e.reason}"
    except Exception as e:
        return False, str(e)


def _send_webhook(settings, data):
    url = settings.get("webhook_url", "")
    if not url:
        return False, "Webhook URL nicht konfiguriert"

    if not _is_safe_url(url, allow_localhost=False):
        return False, "Webhook URL muss HTTPS verwenden"

    try:
        req = urllib.request.Request(
            url,  # NOSONAR - validated by _is_safe_url
            data=json_module.dumps(data).encode(_ENC_UTF8),
            headers={"Content-Type": _CONTENT_TYPE_JSON}
        )
        with urllib.request.urlopen(req, timeout=15) as resp:  # nosec B310 # NOSONAR
            return True, None
    except urllib.error.HTTPError as e:
        err_body = e.read().decode(_ENC_UTF8) if e.fp else ""
        return False, f"Webhook HTTP {e.code}: {err_body[:100]}"
    except urllib.error.URLError as e:
        return False, f"Webhook nicht erreichbar: {e.reason}"
    except Exception as e:
        return False, str(e)


def _send_email(settings, subject, body):
    smtp = settings.get("email_smtp", "")
    user = settings.get("email_user", "")
    pwd = settings.get(_KEY_EMAIL_PASS, "")
    to_addr = settings.get("email_to", "")
    port = settings.get("email_port", 587)
    use_tls = settings.get("email_use_tls", True)

    if not smtp or not user or not to_addr:
        return False, "E-Mail nicht konfiguriert"

    try:
        msg = MIMEMultipart()
        msg['From'] = user
        msg['To'] = to_addr
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain', _ENC_UTF8))

        if use_tls:
            with smtplib.SMTP(smtp, port, timeout=30) as server:
                server.starttls()
                server.login(user, pwd)
                server.sendmail(user, to_addr, msg.as_string())
        else:
            with smtplib.SMTP_SSL(smtp, 465, timeout=30) as server:
                server.login(user, pwd)
                server.sendmail(user, to_addr, msg.as_string())

        return True, None
    except Exception as e:
        return False, str(e)


def _pick(row, key, idx):
    try:
        if isinstance(row, (list, tuple)):
            return row[idx]
    except Exception:
        pass
    try:
        if isinstance(row, dict):
            return row.get(key)
    except Exception:
        pass
    try:
        return row[key]
    except Exception:
        pass
    return None


def _get_allowed_ip_labels(username_filter):
    allowed_ip_labels = {}
    try:
        conn_l = get_db_connection()
        c_l = conn_l.cursor()
        try:
            if username_filter:
                c_l.execute("SELECT ip, COALESCE(label,'') as label FROM user_allowed_ips WHERE lower(username)=lower(?)", (username_filter,))
            else:
                c_l.execute("SELECT ip, COALESCE(label,'') as label FROM user_allowed_ips")
            lrows = c_l.fetchall() or []
        finally:
            conn_l.close()
        for r in lrows:
            ip = _pick(r, 'ip', 0)
            label = _pick(r, 'label', 1)
            ip = str(ip or '').strip()
            label = str(label or '').strip()
            if ip and label:
                allowed_ip_labels[ip] = label
    except Exception:
        pass
    return allowed_ip_labels


def _get_low_stock_items():
    conn = get_db_connection()
    c = conn.cursor()
    try:
        c.execute("""
            SELECT p.id, p.name, COALESCE(i.quantity, 0) as stock, p.min_stock
            FROM products p
            LEFT JOIN inventory i ON p.id = i.product_id
            WHERE p.min_stock > 0 AND COALESCE(i.quantity, 0) < p.min_stock
        """)
        low_stock = c.fetchall()
    except Exception as e:
        print(f"[Notifications] DB-Fehler: {e}")
        return []
    finally:
        conn.close()
    return low_stock if low_stock else []


def _check_new_logins(settings, username_filter, allowed_ip_labels):
    login_msgs = []
    if not settings.get("notify_login", True):
        return login_msgs
    
    try:
        conn_s = get_db_connection()
        c_s = conn_s.cursor()
        try:
            if username_filter:
                c_s.execute("SELECT sid, username, created, ip, ua FROM sessions WHERE lower(username)=lower(?) ORDER BY created ASC", (username_filter,))
            else:
                c_s.execute("SELECT sid, username, created, ip, ua FROM sessions ORDER BY created ASC")
            srows = c_s.fetchall() or []
        finally:
            conn_s.close()
        last_sids = set(settings.get("last_sessions", []) or [])
        current_sids = []
        for r in srows:
            sid = _pick(r, 'sid', 0)
            uname = _pick(r, 'username', 1)
            ip = _pick(r, 'ip', 3)
            ua = _pick(r, 'ua', 4)
            sid = str(sid or '').strip()
            if not sid:
                continue
            current_sids.append(sid)
            if sid in last_sids:
                continue
            uname = str(uname or '').strip() or 'Unbekannt'
            ip = str(ip or '').strip() or 'IP unbekannt'
            ua = str(ua or '').strip()
            label = allowed_ip_labels.get(ip, '')
            extra = f" · {ua}" if ua else ""
            if label:
                login_msgs.append(f"🔐 Anmeldung: {uname} · {label} ({ip}){extra}")
            else:
                login_msgs.append(f"🔐 Anmeldung: {uname} · {ip}{extra}")
        settings["last_sessions"] = list(current_sids)[-500:]
    except Exception:
        pass
    return login_msgs


def _check_new_trusted_devices(settings, username_filter):
    trusted_msgs = []
    notify_trusted = settings.get("notify_new_trusted_device", True)
    notify_trusted_manual = settings.get("notify_new_trusted_device_manual", True)
    if not (notify_trusted or notify_trusted_manual):
        return trusted_msgs
    
    try:
        conn2 = get_db_connection()
        c2 = conn2.cursor()
        try:
            if username_filter:
                c2.execute("SELECT username, ip, COALESCE(label,'') as label FROM user_allowed_ips WHERE lower(username)=lower(?)", (username_filter,))
            else:
                c2.execute("SELECT username, ip, COALESCE(label,'') as label FROM user_allowed_ips")
            rows = c2.fetchall() or []
        finally:
            conn2.close()
        last_raw = settings.get("last_allowed_ips", []) or []
        last = set()
        for x in last_raw:
            try:
                s = str(x or '')
            except Exception:
                continue
            if '|' in s:
                u, ipx = s.split('|', 1)
                last.add(u.strip().lower() + '|' + ipx.strip())
            else:
                last.add(s.strip())
        current = set()
        for r in rows:
            uname = _pick(r, 'username', 0)
            ip = _pick(r, 'ip', 1)
            label = _pick(r, 'label', 2)
            uname = str(uname or '').strip()
            ip = str(ip or '').strip()
            label = str(label or '').strip()
            if not uname or not ip:
                continue
            key = uname.lower() + "|" + ip
            current.add(key)
            if key in last:
                continue
            is_manual = bool(label)
            if is_manual and notify_trusted_manual:
                trusted_msgs.append(f"✅ Neues vertrauenswürdiges Gerät/IP manuell hinzugefügt: {uname} · {ip} ({label})")
            elif (not is_manual) and notify_trusted:
                trusted_msgs.append(f"✅ Neues vertrauenswürdiges Gerät/IP automatisch freigegeben: {uname} · {ip}")
        settings["last_allowed_ips"] = list(current)
    except Exception:
        pass
    return trusted_msgs


def _build_notification_message(new_low, trusted_msgs, login_msgs):
    message_parts = []
    subject_parts = []
    if new_low:
        lines = ["⚠️ <b>Niedriger Lagerbestand</b>", ""]
        for item in new_low:
            name, stock, min_s = item[1], item[2], item[3]
            lines.append(f"• {name}: {stock} / {min_s} Stk")
        message_parts.append("\n".join(lines))
        subject_parts.append(f"⚠️ {len(new_low)} Artikel unter Mindestbestand")
    if trusted_msgs:
        message_parts.append("\n".join(trusted_msgs))
        subject_parts.append("Neues vertrauenswürdiges Gerät/IP")
    if login_msgs:
        message_parts.append("\n".join(login_msgs))
        subject_parts.append("Neue Anmeldung")
    message = "\n\n".join([p for p in message_parts if p])
    subject = " · ".join([p for p in subject_parts if p]) or "Lagerverwaltung Benachrichtigung"
    return message, subject


def _send_notifications(settings, message, subject, new_low):
    errors = []
    if settings.get("telegram_enabled"):
        _, err = _send_telegram(settings, message)
        if err:
            errors.append(f"Telegram: {err}")
    if settings.get("discord_enabled"):
        discord_msg = message.replace("<b>", "**").replace("</b>", "**")
        _, err = _send_discord(settings, discord_msg)
        if err:
            errors.append(f"Discord: {err}")
    if settings.get("webhook_enabled"):
        data = {
            "type": "low_stock",
            "count": len(new_low),
            "items": [{"name": r[1], "stock": r[2], "min_stock": r[3]} for r in new_low],
            "timestamp": int(time_module.time() * 1000)
        }
        _, err = _send_webhook(settings, data)
        if err:
            errors.append(f"Webhook: {err}")
    if settings.get("email_enabled"):
        body = message.replace("<b>", "").replace("</b>", "")
        _, err = _send_email(settings, subject, body)
        if err:
            errors.append(f"E-Mail: {err}")
    if errors:
        print(f"[Notifications] Fehler: {', '.join(errors)}")


def _check_and_notify():
    settings = _get_notify_settings()
    if not settings.get("enabled", True):
        return

    username_filter = str(settings.get("notify_username_filter", "") or "").strip()
    allowed_ip_labels = _get_allowed_ip_labels(username_filter)
    low_stock = _get_low_stock_items()

    current_ids = {r[0] for r in low_stock}
    last_ids = set(settings.get("last_low_stock", []))
    new_low = [r for r in low_stock if r[0] not in last_ids]

    if not new_low:
        settings["last_low_stock"] = list(current_ids)

    login_msgs = _check_new_logins(settings, username_filter, allowed_ip_labels)
    trusted_msgs = _check_new_trusted_devices(settings, username_filter)

    if (not new_low) and (not trusted_msgs) and (not login_msgs):
        _save_notify_settings(settings)
        return

    message, subject = _build_notification_message(new_low, trusted_msgs, login_msgs)
    _send_notifications(settings, message, subject, new_low)

    settings["last_low_stock"] = list(current_ids)
    _save_notify_settings(settings)


def _background_checker():
    while True:
        try:
            if not _is_plugin_manager_enabled('low_stock_notifications'):
                time_module.sleep(30)
                continue
            settings = _get_notify_settings()
            interval = settings.get("check_interval", 60)
            try:
                interval = int(interval)
            except Exception:
                interval = 60
            if interval < 5:
                interval = 5
            if interval > 3600:
                interval = 3600
            _check_and_notify()
            time_module.sleep(interval)
        except Exception as e:
            print(f"[Notifications] Checker error: {e}")
            time_module.sleep(60)


@plugin_blueprint.route("/settings", methods=["GET"])
@require_auth()
def get_settings():
    settings = _get_notify_settings()
    if settings.get(_KEY_TG_TOKEN):
        settings["telegram_token_masked"] = _mask_secret(settings.get(_KEY_TG_TOKEN))
        settings[_KEY_TG_TOKEN] = ""
    if settings.get(_KEY_EMAIL_PASS):
        settings["email_pass_masked"] = _MASKED
        settings[_KEY_EMAIL_PASS] = ""
    return json_response({"status": "ok", "settings": settings})


@plugin_blueprint.route("/settings", methods=["POST"])
@require_auth()
def save_settings():
    data = request.json or {}
    current = _get_notify_settings()

    keys = [
        "enabled", "check_interval",
        "notify_username_filter",
        "notify_login", "notify_ip_change", "notify_new_trusted_device", "notify_new_trusted_device_manual", "notify_pin_change", "notify_stock_change", "notify_low_stock",
        "telegram_enabled", _KEY_TG_TOKEN, _KEY_TG_CHAT, "telegram_requests_enabled",
        "discord_enabled", "discord_webhook",
        "webhook_enabled", "webhook_url",
        "email_enabled", "email_smtp", "email_port", "email_user", _KEY_EMAIL_PASS, "email_to", "email_use_tls",
    ]

    for key in keys:
        if key not in data:
            continue
        if key in (_KEY_TG_TOKEN, _KEY_EMAIL_PASS):
            if _is_masked_secret(data.get(key)):
                continue
        current[key] = data.get(key)

    _save_notify_settings(current)
    return json_response({"status": "ok"})


@plugin_blueprint.route("/low-stock", methods=["GET"])
@require_auth()
def get_low_stock():
    conn = get_db_connection()
    c = conn.cursor()
    try:
        c.execute("""
            SELECT p.id, p.name, COALESCE(i.quantity, 0) as stock, p.min_stock
            FROM products p
            LEFT JOIN inventory i ON p.id = i.product_id
            WHERE p.min_stock > 0 AND COALESCE(i.quantity, 0) < p.min_stock
            ORDER BY (p.min_stock - COALESCE(i.quantity, 0)) DESC, p.name
        """)
        rows = c.fetchall() or []
        low = [{"id": r[0], "name": r[1], "stock": r[2], "min_stock": r[3]} for r in rows]
        return json_response({"status": "ok", "low_stock": low})
    finally:
        conn.close()


@plugin_blueprint.route("/check", methods=["POST"])
@require_auth()
def manual_check():
    try:
        _check_and_notify()
        return json_response({"status": "ok"})
    except Exception as e:
        return json_response({"status": "error", "message": str(e)})


@plugin_blueprint.route("/test", methods=["POST"])
@require_auth()
def test_notification():
    data = request.json or {}
    ntype = data.get("type", "")
    settings = _get_notify_settings()
    tmp = dict(settings)

    if ntype == "telegram":
        if _KEY_TG_TOKEN in data and not _is_masked_secret(data.get(_KEY_TG_TOKEN)):
            tmp[_KEY_TG_TOKEN] = data.get(_KEY_TG_TOKEN)
        if _KEY_TG_CHAT in data:
            tmp[_KEY_TG_CHAT] = data.get(_KEY_TG_CHAT)
        _, err = _send_telegram(tmp, "✅ Telegram Test erfolgreich")
    elif ntype == "discord":
        if "discord_webhook" in data:
            tmp["discord_webhook"] = data.get("discord_webhook")
        _, err = _send_discord(tmp, "✅ Discord Test erfolgreich")
    elif ntype == "webhook":
        if "webhook_url" in data:
            tmp["webhook_url"] = data.get("webhook_url")
        _, err = _send_webhook(tmp, {"type": "test", "message": "Webhook Test erfolgreich", "ts": int(time_module.time() * 1000)})
    elif ntype == "email":
        for k in ("email_smtp", "email_port", "email_user", _KEY_EMAIL_PASS, "email_to", "email_use_tls"):
            if k in data:
                if k == _KEY_EMAIL_PASS and _is_masked_secret(data.get(k)):
                    continue
                tmp[k] = data.get(k)
        _, err = _send_email(tmp, "Lagerverwaltung Test", "E-Mail Test erfolgreich")
    else:
        return json_response({"status": "error", "message": "Unbekannter Typ"})

    if err:
        return json_response({"status": "error", "message": err})
    return json_response({"status": "ok"})


def _get_telegram_updates(settings):
    token = settings.get(_KEY_TG_TOKEN, "")
    if not token:
        return []

    last_update_id = settings.get("telegram_last_update_id", 0)

    url = f"https://api.telegram.org/bot{token}/getUpdates"
    if not _is_safe_url(url, allow_localhost=False):
        print("[Telegram] URL ungültig")
        return []
    params = {
        "offset": last_update_id + 1 if last_update_id else 0,
        "timeout": 0,
        "limit": 10
    }

    try:
        req_url = url + "?" + "&".join(f"{k}={v}" for k, v in params.items())
        req = urllib.request.Request(req_url)
        with urllib.request.urlopen(req, timeout=10) as resp:  # nosec B310 # validated by _is_safe_url
            data = json_module.loads(resp.read().decode(_ENC_UTF8))
            if data.get("ok"):
                return data.get("result", [])
    except Exception as e:
        print(f"[Telegram] GetUpdates Fehler: {e}")
    return []


def _process_telegram_updates():
    settings = _get_notify_settings()
    if not settings.get("telegram_requests_enabled", True):
        return
    
    updates = _get_telegram_updates(settings)
    if not updates:
        return
    
    pending = settings.get(_KEY_TG_PENDING, [])
    existing_chat_ids = {r.get("chat_id") for r in pending}
    
    for update in updates:
        settings["telegram_last_update_id"] = update.get("update_id", 0)
        
        message = update.get("message") or update.get("edited_message")
        if not message:
            continue
        
        chat = message.get("chat", {})
        chat_id = str(chat.get("id", ""))
        chat_type = chat.get("type", "private")
        
        from_user = message.get("from", {})
        username = from_user.get("username") or from_user.get("first_name") or f"User{chat_id}"
        
        text = message.get("text", "").strip()
        
        if text == "/start":
            if chat_id and chat_id not in existing_chat_ids and chat_id != settings.get(_KEY_TG_CHAT):
                pending.append({
                    "chat_id": chat_id,
                    "username": username,
                    "chat_type": chat_type,
                    "timestamp": int(time_module.time() * 1000),
                    "status": "pending"
                })
                existing_chat_ids.add(chat_id)
                print(f"[Telegram] Neue Anfrage von {username} (Chat-ID: {chat_id})")
    
    if pending != settings.get(_KEY_TG_PENDING, []):
        settings[_KEY_TG_PENDING] = pending
        _save_notify_settings(settings)


def _telegram_request_poller():
    while True:
        try:
            if not _is_plugin_manager_enabled('low_stock_notifications'):
                time_module.sleep(30)
                continue
            _process_telegram_updates()
            time_module.sleep(5)
        except Exception as e:
            print(f"[Telegram] Poller error: {e}")
            time_module.sleep(30)


@plugin_blueprint.route("/telegram/requests", methods=["GET"])
@require_auth()
def get_telegram_requests():
    settings = _get_notify_settings()
    requests = settings.get(_KEY_TG_PENDING, [])
    return json_response({"status": "ok", "requests": requests})


@plugin_blueprint.route("/telegram/requests/<chat_id>", methods=["POST"])
@require_auth()
def handle_telegram_request(chat_id):
    data = request.json or {}
    action = data.get("action", "accept")
    
    settings = _get_notify_settings()
    pending = settings.get(_KEY_TG_PENDING, [])
    
    request_item = None
    for r in pending:
        if str(r.get("chat_id")) == str(chat_id):
            request_item = r
            break
    
    if not request_item:
        return json_response({"status": "error", "message": "Anfrage nicht gefunden"})
    
    if action == "accept":
        settings[_KEY_TG_CHAT] = str(chat_id)
        settings["telegram_enabled"] = True
        
        settings[_KEY_TG_PENDING] = [r for r in pending if str(r.get("chat_id")) != str(chat_id)]
        _save_notify_settings(settings)
        
        msg = f"✅ Hallo {request_item.get('username', 'User')}!\n\nDeine Anfrage wurde akzeptiert. Du erhältst jetzt Benachrichtigungen von der Lagerverwaltung."
        _send_telegram(settings, msg)
        
        return json_response({"status": "ok", "message": f"Chat-ID {chat_id} übernommen"})
    
    elif action == "reject":
        settings[_KEY_TG_PENDING] = [r for r in pending if str(r.get("chat_id")) != str(chat_id)]
        _save_notify_settings(settings)
        
        temp_settings = {_KEY_TG_TOKEN: settings.get(_KEY_TG_TOKEN), _KEY_TG_CHAT: str(chat_id)}
        msg = f"❌ Hallo {request_item.get('username', 'User')}!\n\nDeine Anfrage wurde abgelehnt."
        _send_telegram(temp_settings, msg)
        
        return json_response({"status": "ok", "message": "Anfrage abgelehnt"})
    
    return json_response({"status": "error", "message": "Unbekannte Aktion"})

try:
    if not _threads_started:
        _threads_started = True
        _checker_thread = threading.Thread(target=_background_checker, daemon=True)
        _checker_thread.start()
except Exception as e:
    print(f"[Notifications] Konnte Background-Thread nicht starten: {e}")

try:
    if _threads_started:
        _telegram_thread = threading.Thread(target=_telegram_request_poller, daemon=True)
        _telegram_thread.start()
except Exception as e:
    print(f"[Telegram] Konnte Poller-Thread nicht starten: {e}")
