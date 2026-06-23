"""
SSO Plugin fuer LagerSync
--------------------------
Fuegt Login per OpenID Connect (OIDC) hinzu.

Funktioniert mit jedem standardkonformen OIDC-Provider (Authentik, Keycloak,
Auth0, Microsoft Entra ID, Google, ...) - die tatsaechlichen Login/Token/
Userinfo-Adressen werden automatisch per OIDC-Discovery von der Issuer-URL
abgefragt (/.well-known/openid-configuration), nicht fest einprogrammiert.

WICHTIG: Dieses Plugin enthaelt KEINE Zugangsdaten. Issuer-URL, Client-ID,
Client-Secret und Button-Text werden nach der Installation ueber das
Einstellungen-Menue (Zahnrad-Icon in der App) konfiguriert und lokal in
einer eigenen Tabelle gespeichert - niemals im Code oder auf GitHub.
"""

import time
import secrets
from urllib.parse import urlencode

import requests
from flask import Blueprint, redirect

plugin_blueprint = Blueprint('sso', __name__)

CONFIG_KEYS = ['issuer', 'client_id', 'client_secret', 'button_text', 'autocreate']

ADMIN_ONLY_MSG = 'Nur fuer Administratoren'
CALLBACK_PATH = '/callback'

_discovery_cache = {}  # issuer -> (timestamp, discovery_dict)
_DISCOVERY_CACHE_SECONDS = 300


def _init_table():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS sso_config (
        key TEXT PRIMARY KEY,
        value TEXT
    )''')
    conn.commit()
    conn.close()


try:
    _init_table()
except Exception as e:
    print(f'[sso] DB-Init Fehler: {e}')


def _get_config():
    conn = get_db_connection()
    c = conn.cursor()
    try:
        c.execute('SELECT key, value FROM sso_config')
        cfg = {row['key']: row['value'] for row in c.fetchall()}
    finally:
        conn.close()
    return {
        'issuer': cfg.get('issuer', ''),
        'client_id': cfg.get('client_id', ''),
        'client_secret': cfg.get('client_secret', ''),
        'button_text': cfg.get('button_text') or 'Mit SSO anmelden',
        'autocreate': cfg.get('autocreate', 'true') == 'true',
    }


def _save_config(data):
    conn = get_db_connection()
    c = conn.cursor()
    try:
        for key in CONFIG_KEYS:
            if key not in data:
                continue
            value = data[key]
            if key == 'autocreate':
                value = 'true' if value else 'false'
            c.execute(
                'INSERT INTO sso_config (key, value) VALUES (?, ?) '
                'ON CONFLICT(key) DO UPDATE SET value=excluded.value',
                (key, str(value))
            )
        conn.commit()
    finally:
        conn.close()


def _is_admin_request():
    user = session.get('user')
    name = user.get('name') if isinstance(user, dict) else None
    return bool(name and user_is_admin(name))


def _discover(issuer):
    """Fragt die OIDC-Discovery-Dokumente des Providers ab (mit kurzem Cache).
    Funktioniert mit jedem standardkonformen OIDC-Provider, unabhaengig
    davon, welche URL-Struktur er intern verwendet."""
    issuer = issuer.rstrip('/')
    now = time.time()
    cached = _discovery_cache.get(issuer)
    if cached and now - cached[0] < _DISCOVERY_CACHE_SECONDS:
        return cached[1]

    resp = requests.get(f"{issuer}/.well-known/openid-configuration", timeout=10)
    resp.raise_for_status()
    doc = resp.json()
    _discovery_cache[issuer] = (now, doc)
    return doc


# ---------- Admin: Konfiguration lesen/speichern ----------

@plugin_blueprint.route('/config', methods=['GET'])
@require_auth()
def get_config():
    if not _is_admin_request():
        return json_response({'error': ADMIN_ONLY_MSG}, 403)
    cfg = _get_config()
    cfg['client_secret'] = bool(cfg['client_secret'])  # nie den echten Wert zurueckgeben
    return json_response(cfg)


@plugin_blueprint.route('/config', methods=['POST'])
@require_auth()
def save_config():
    if not _is_admin_request():
        return json_response({'error': ADMIN_ONLY_MSG}, 403)
    data = request.get_json(silent=True) or {}
    _save_config(data)
    return json_response({'status': 'ok'})


@plugin_blueprint.route('/test-issuer', methods=['POST'])
@require_auth()
def test_issuer():
    """Prueft ob eine Issuer-URL gueltige OIDC-Discovery-Daten liefert
    (fuer den 'Testen'-Knopf in den Einstellungen)."""
    if not _is_admin_request():
        return json_response({'error': ADMIN_ONLY_MSG}, 403)
    data = request.get_json(silent=True) or {}
    issuer = (data.get('issuer') or '').strip()
    if not issuer:
        return json_response({'ok': False, 'error': 'Keine Issuer-URL angegeben'}, 400)
    try:
        doc = _discover(issuer)
        required = ['authorization_endpoint', 'token_endpoint', 'userinfo_endpoint']
        missing = [k for k in required if k not in doc]
        if missing:
            return json_response({'ok': False, 'error': f'Discovery-Dokument unvollstaendig (fehlt: {", ".join(missing)})'})
        return json_response({'ok': True})
    except Exception as e:
        return json_response({'ok': False, 'error': str(e)})


# ---------- Oeffentlich: Button-Text fuer die Login-Seite ----------

@plugin_blueprint.route('/public-config', methods=['GET'])
def public_config():
    cfg = _get_config()
    configured = bool(cfg['issuer'] and cfg['client_id'] and cfg['client_secret'])
    return json_response({'configured': configured, 'button_text': cfg['button_text']})


# ---------- SSO Login starten ----------

@plugin_blueprint.route('/login', methods=['GET'])
def sso_login():
    cfg = _get_config()
    if not (cfg['issuer'] and cfg['client_id'] and cfg['client_secret']):
        return 'SSO ist noch nicht konfiguriert. Bitte einen Administrator kontaktieren.', 503

    try:
        discovery = _discover(cfg['issuer'])
        authorize_endpoint = discovery['authorization_endpoint']
    except Exception as e:
        return f'Provider nicht erreichbar oder Discovery fehlgeschlagen: {e}', 502

    state = secrets.token_urlsafe(24)
    session['sso_state'] = state
    session['sso_state_ts'] = time.time()

    prefix = request.path.rsplit('/login', 1)[0]
    redirect_uri = request.host_url.rstrip('/') + prefix + CALLBACK_PATH

    params = {
        'response_type': 'code',
        'client_id': cfg['client_id'],
        'redirect_uri': redirect_uri,
        'scope': 'openid email profile',
        'state': state,
    }
    sep = '&' if '?' in authorize_endpoint else '?'
    auth_url = f"{authorize_endpoint}{sep}{urlencode(params)}"
    return redirect(auth_url)


# ---------- SSO Callback ----------

@plugin_blueprint.route(CALLBACK_PATH, methods=['GET'])
def sso_callback():  # NOSONAR - OIDC callback orchestration, intentional complexity
    cfg = _get_config()

    oidc_error = request.args.get('error')
    if oidc_error:
        return f'Anmeldung abgebrochen: {oidc_error}', 400

    code = request.args.get('code')
    state = request.args.get('state')
    expected_state = session.pop('sso_state', None)
    state_ts = session.pop('sso_state_ts', 0)

    if not code or not state or state != expected_state:
        return 'Ungueltige oder abgelaufene Anfrage. Bitte erneut versuchen.', 400
    if time.time() - state_ts > 600:
        return 'Anfrage abgelaufen. Bitte erneut versuchen.', 400

    try:
        discovery = _discover(cfg['issuer'])
        token_endpoint = discovery['token_endpoint']
        userinfo_endpoint = discovery['userinfo_endpoint']
    except Exception as e:
        return f'Provider nicht erreichbar oder Discovery fehlgeschlagen: {e}', 502

    prefix = request.path.rsplit(CALLBACK_PATH, 1)[0]
    redirect_uri = request.host_url.rstrip('/') + prefix + CALLBACK_PATH

    try:
        token_resp = requests.post(
            token_endpoint,
            data={
                'grant_type': 'authorization_code',
                'code': code,
                'redirect_uri': redirect_uri,
                'client_id': cfg['client_id'],
                'client_secret': cfg['client_secret'],
            },
            timeout=10,
        )
        token_resp.raise_for_status()
        access_token = token_resp.json().get('access_token')
        if not access_token:
            return 'Token-Austausch fehlgeschlagen (kein access_token erhalten).', 502

        userinfo_resp = requests.get(
            userinfo_endpoint,
            headers={'Authorization': f'Bearer {access_token}'},
            timeout=10,
        )
        userinfo_resp.raise_for_status()
        userinfo = userinfo_resp.json()
    except requests.RequestException as e:
        return f'Verbindung zum Provider fehlgeschlagen: {e}', 502

    username_claim = userinfo.get('preferred_username') or userinfo.get('email') or userinfo.get('sub')
    if not username_claim:
        return 'Der Provider hat keinen verwendbaren Benutzernamen geliefert.', 502

    canon = canonical_username(username_claim) or username_claim

    conn = get_db_connection()
    c = conn.cursor()
    try:
        c.execute('SELECT username, role, permissions FROM users WHERE username = ?', (canon,))
        row = c.fetchone()

        if not row:
            if not cfg['autocreate']:
                conn.close()
                return 'Kein passender LagerSync-Account gefunden. Bitte einen Administrator kontaktieren.', 403
            c.execute(
                'INSERT OR IGNORE INTO users (username, pin, pin_hash, role, permissions) VALUES (?, ?, ?, ?, ?)',
                (canon, '', '', 'user', None)
            )
            conn.commit()
            c.execute('SELECT username, role, permissions FROM users WHERE username = ?', (canon,))
            row = c.fetchone()

        user_obj = {'name': row['username'], 'role': row['role'] or 'user', 'id': row['username']}
        perms_obj = normalize_permissions_value(row['permissions'])
        if perms_obj is not None:
            user_obj['permissions'] = perms_obj
    finally:
        conn.close()

    session.pop('demo', None)
    session['user'] = user_obj
    try:
        session.permanent = True
    except Exception:
        pass
    try:
        session['sid'] = register_session(user_obj['id'])
        enforce_max_devices(user_obj['id'])
        try:
            refresh_ip_whitelist_for(user_obj['id'])
            cleanup_other_sessions_for(user_obj['id'], session.get('sid') or '')
        except Exception:
            pass
    except Exception:
        pass

    return redirect('/')
