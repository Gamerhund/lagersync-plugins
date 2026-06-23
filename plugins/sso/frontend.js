if (document.readyState === 'loading') {
    await new Promise(resolve => document.addEventListener('DOMContentLoaded', resolve));
}

const pluginId = window.pluginId || 
                 document.currentScript?.src?.match(/plugin\/([^/]+)/)?.[1] || 
                 'sso';

try {
    const resp = await PluginAPI.fetch(pluginId, '/public-config');
    const cfg = await resp.json();

    if (cfg.configured) {
        const target = document.querySelector('#pinScreen') ||
                      document.querySelector('.login-screen') ||
                      document.querySelector('.pin-screen') ||
                      document.querySelector('.auth-screen');

        if (target && !document.getElementById('sso-login-btn')) {
            const btn = document.createElement('button');
            btn.id = 'sso-login-btn';
            btn.className = 'btn';
            btn.style.cssText = 'width:100%;margin-top:16px;display:flex;align-items:center;justify-content:center;gap:8px;';
            btn.innerHTML = '🔐 ' + (cfg.button_text || 'Mit SSO anmelden');
            btn.onclick = () => window.location.href = `/api/plugin/${pluginId}/login`;
            target.appendChild(btn);
        }
    }
} catch (e) {
    console.error('[sso] Button Fehler:', e);
}

PluginAPI.addMenuItem('SSO', '🔐', async function () {
    const m = document.createElement('div');
    m.className = 'modal';
    m.style.display = 'flex';
    m.innerHTML = `
        <div class="modal-content" style="max-width:520px;width:95vw">
            <h3>🔐 SSO Einstellungen</h3>
            <div id="sso-status" style="margin-bottom:10px;color:#888;font-size:0.9em">Lade...</div>
            
            <div style="display:flex;flex-direction:column;gap:12px">
                <label>Issuer-URL<br><input id="sso-issuer" type="text" style="width:100%" placeholder="https://..."></label>
                <button class="btn" id="sso-test" style="align-self:flex-start">Verbindung testen</button>
                <div id="sso-test-result" style="font-size:0.85em"></div>

                <label>Client-ID<br><input id="sso-client-id" type="text" style="width:100%"></label>
                <label>Client-Secret<br><input id="sso-client-secret" type="password" style="width:100%" placeholder="leer lassen = unverändert"></label>
                <label>Button-Text<br><input id="sso-button-text" type="text" style="width:100%"></label>
                
                <label>Username Claim<br>
                    <select id="sso-username-claim" style="width:100%">
                        <option value="preferred_username">preferred_username</option>
                        <option value="email">email</option>
                        <option value="sub">sub</option>
                        <option value="name">name</option>
                    </select>
                </label>
                
                <label>Scope<br><input id="sso-scope" type="text" style="width:100%" placeholder="openid email profile"></label>
                
                <div style="display:flex;gap:12px">
                    <label style="display:flex;align-items:center;gap:6px"><input id="sso-autocreate" type="checkbox"> Neue User automatisch anlegen</label>
                    <label style="display:flex;align-items:center;gap:6px"><input id="sso-debug" type="checkbox"> Debug-Modus</label>
                </div>
            </div>

            <div style="margin-top:20px;display:flex;gap:8px;flex-wrap:wrap">
                <button class="btn" id="sso-save">Speichern</button>
                <button class="btn" id="sso-reset">Zurücksetzen</button>
                <button class="btn" onclick="this.closest('.modal').remove()">Schließen</button>
                <button class="btn" id="sso-logout" style="margin-left:auto">Abmelden</button>
            </div>
        </div>`;

    document.body.appendChild(m);
    m.addEventListener('click', e => { if (e.target === m) m.remove(); });

    const statusEl = document.getElementById('sso-status');
    const testEl = document.getElementById('sso-test-result');

    try {
        const resp = await PluginAPI.fetch(pluginId, '/config');
        if (resp.status === 403) {
            statusEl.textContent = 'Nur für Administratoren sichtbar.';
            return;
        }
        const cfg = await resp.json();

        document.getElementById('sso-issuer').value = cfg.issuer || '';
        document.getElementById('sso-client-id').value = cfg.client_id || '';
        document.getElementById('sso-button-text').value = cfg.button_text || '';
        document.getElementById('sso-scope').value = cfg.scope || 'openid email profile';
        document.getElementById('sso-username-claim').value = cfg.username_claim || 'preferred_username';
        document.getElementById('sso-autocreate').checked = !!cfg.autocreate;
        document.getElementById('sso-debug').checked = !!cfg.debug_mode;
        statusEl.textContent = '';
    } catch (e) {
        statusEl.textContent = 'Fehler beim Laden: ' + e.message;
    }

    document.getElementById('sso-test').onclick = async () => {
        const issuer = document.getElementById('sso-issuer').value.trim();
        testEl.textContent = 'Teste...';
        try {
            const resp = await PluginAPI.fetch(pluginId, '/test-issuer', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({issuer})
            });
            const r = await resp.json();
            testEl.textContent = r.ok ? '✅ Erfolgreich' : '❌ ' + (r.error || 'Fehler');
            testEl.style.color = r.ok ? '#4caf50' : '#e53935';
        } catch(e) {
            testEl.textContent = '❌ ' + e.message;
        }
    };

    document.getElementById('sso-save').onclick = async () => {
        const body = {
            issuer: document.getElementById('sso-issuer').value.trim(),
            client_id: document.getElementById('sso-client-id').value.trim(),
            button_text: document.getElementById('sso-button-text').value.trim(),
            username_claim: document.getElementById('sso-username-claim').value,
            scope: document.getElementById('sso-scope').value.trim(),
            autocreate: document.getElementById('sso-autocreate').checked,
            debug_mode: document.getElementById('sso-debug').checked,
        };
        const secret = document.getElementById('sso-client-secret').value.trim();
        if (secret) body.client_secret = secret;

        try {
            const resp = await PluginAPI.fetch(pluginId, '/config', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(body)
            });
            if (!resp.ok) throw new Error('HTTP ' + resp.status);
            if (typeof showToast === 'function') showToast('✅ Gespeichert');
            else alert('✅ Gespeichert');
            m.remove();
        } catch(e) {
            if (typeof showToast === 'function') showToast('❌ ' + e.message, 'error');
            else alert('❌ ' + e.message);
        }
    };

    document.getElementById('sso-reset').onclick = () => { if(confirm('Konfiguration wirklich zurücksetzen?')) location.reload(); };
    document.getElementById('sso-logout').onclick = () => window.location.href = `/api/plugin/${pluginId}/logout`;
});