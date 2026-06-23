import time
import secrets
from urllib.parse import urlencode

import requests
from flask import Blueprint, redirect, request

plugin_blueprint = Blueprint('sso', __name__)

CONFIG_KEYS = ['issuer', 'client_id', 'client_secret', 'button_text', 'autocreate',
               'username_claim', 'scope', 'debug_mode']

ADMIN_ONLY_MSG = 'Nur für Administratoren'
CALLBACK_PATH = '/callback'
LOGOUT_PATH = '/logout'

_discovery_cache = {}
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
        'username_claim': cfg.get('username_claim') or 'preferred_username',
        'scope': cfg.get('scope') or 'openid email profile',
        'debug_mode': cfg.get('debug_mode', 'false') == 'true',
    }


def _save_config(data):
    conn = get_db_connection()
    c = conn.cursor()
    try:
        for key in CONFIG_KEYS:
            if key not in data:
                continue
            value = data[key]
            if key in ('autocreate', 'debug_mode'):
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


@plugin_blueprint.route('/config', methods=['GET'])
@require_auth()
def get_config():
    if not _is_admin_request():
        return json_response({'error': ADMIN_ONLY_MSG}, 403)
    cfg = _get_config()
    cfg['client_secret'] = bool(cfg['client_secret'])
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
    if not _is_admin_request():
        return json_response({'error': ADMIN_ONLY_MSG}, 403)
    data = request.get_json(silent=True) or {}
    issuer = (data.get('issuer') or '').strip()
    if not issuer:
        return json_response({'ok': False, 'error': 'Keine Issuer-URL angegeben'}, 400)
    try:
        doc = _discover(issuer)
        required = ['authorization_endpoint', 'token_endpoint', 'userinfo_endpoint']
        if any(k not in doc for k in required):
            return json_response({'ok': False, 'error': 'Discovery-Dokument unvollständig'})
        return json_response({'ok': True})
    except Exception as e:
        return json_response({'ok': False, 'error': str(e)})


@plugin_blueprint.route('/public-config', methods=['GET'])
def public_config():
    cfg = _get_config()
    configured = bool(cfg['issuer'] and cfg['client_id'] and cfg['client_secret'])
    return json_response({'configured': configured, 'button_text': cfg['button_text']})


@plugin_blueprint.route('/login', methods=['GET'])
def sso_login():
    cfg = _get_config()
    if not (cfg['issuer'] and cfg['client_id'] and cfg['client_secret']):
        return 'SSO nicht konfiguriert.', 503

    try:
        discovery = _discover(cfg['issuer'])
        authorize_endpoint = discovery['authorization_endpoint']
    except Exception as e:
        return f'Discovery fehlgeschlagen: {e}', 502

    state = secrets.token_urlsafe(24)
    nonce = secrets.token_urlsafe(24)

    session['sso_state'] = state
    session['sso_nonce'] = nonce
    session['sso_state_ts'] = time.time()

    prefix = request.path.rsplit('/login', 1)[0]
    redirect_uri = request.host_url.rstrip('/') + prefix + CALLBACK_PATH

    params = {
        'response_type': 'code',
        'client_id': cfg['client_id'],
        'redirect_uri': redirect_uri,
        'scope': cfg['scope'],
        'state': state,
        'nonce': nonce,
    }
    sep = '&' if '?' in authorize_endpoint else '?'
    auth_url = f"{authorize_endpoint}{sep}{urlencode(params)}"
    return redirect(auth_url)


def _validate_callback_params():
    if request.args.get('error'):
        return None, f'Anmeldung abgebrochen: {request.args.get("error")}', 400

    code = request.args.get('code')
    state = request.args.get('state')
    expected_state = session.pop('sso_state', None)
    ts = session.pop('sso_state_ts', 0)

    if not code or not state or state != expected_state or time.time() - ts > 600:
        return None, 'Ungültige oder abgelaufene Anfrage.', 400

    return code, None, None


def _exchange_token(cfg, code):
    try:
        discovery = _discover(cfg['issuer'])
        token_endpoint = discovery['token_endpoint']
        userinfo_endpoint = discovery['userinfo_endpoint']
    except Exception as e:
        return None, f'Discovery fehlgeschlagen: {e}', 502

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
            timeout=10
        )
        token_resp.raise_for_status()
        access_token = token_resp.json().get('access_token')

        userinfo_resp = requests.get(
            userinfo_endpoint,
            headers={'Authorization': f'Bearer {access_token}'},
            timeout=10
        )
        userinfo_resp.raise_for_status()
        return userinfo_resp.json(), None, None
    except Exception as e:
        return None, f'Token-Austausch fehlgeschlagen: {e}', 502


@plugin_blueprint.route(CALLBACK_PATH, methods=['GET'])
def sso_callback():
    cfg = _get_config()
    code, _, error_msg = _validate_callback_params()
    if error_msg:
        return error_msg, 400

    userinfo, error_msg, status = _exchange_token(cfg, code)
    if error_msg:
        return error_msg, status

    claim = cfg['username_claim']
    username = userinfo.get(claim) or userinfo.get('preferred_username') or userinfo.get('email') or userinfo.get('sub')
    if not username:
        return 'Kein Benutzername gefunden.', 502

    canon = canonical_username(username) or username

    if cfg['debug_mode']:
        print(f'[sso] Login für: {username} | Userinfo: {userinfo}')

    conn = get_db_connection()
    c = conn.cursor()
    try:
        c.execute('SELECT username, role, permissions FROM users WHERE username = ?', (canon,))
        row = c.fetchone()

        if not row:
            if not cfg['autocreate']:
                conn.close()
                return 'Kein Account gefunden. Administrator kontaktieren.', 403
            c.execute(
                'INSERT OR IGNORE INTO users (username, pin, pin_hash, role, permissions) VALUES (?, ?, ?, ?, ?)',
                (canon, '', '', 'user', None)
            )
            conn.commit()
            c.execute('SELECT username, role, permissions FROM users WHERE username = ?', (canon,))
            row = c.fetchone()

        user_obj = {'name': row['username'], 'role': row['role'] or 'user', 'id': row['username']}
        perms = normalize_permissions_value(row['permissions'])
        if perms is not None:
            user_obj['permissions'] = perms
    finally:
        conn.close()

    session.pop('demo', None)
    session['user'] = user_obj
    try:
        session.permanent = True
        session['sid'] = register_session(user_obj['id'])
        enforce_max_devices(user_obj['id'])
        refresh_ip_whitelist_for(user_obj['id'])
        cleanup_other_sessions_for(user_obj['id'], session.get('sid') or '')
    except Exception:
        pass

    return redirect('/')


@plugin_blueprint.route(LOGOUT_PATH, methods=['GET'])
def sso_logout():
    session.clear()
    cfg = _get_config()
    try:
        discovery = _discover(cfg['issuer'])
        if 'end_session_endpoint' in discovery:
            return redirect(discovery['end_session_endpoint'])
    except Exception:
        pass
    return redirect('/login')