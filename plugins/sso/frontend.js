if (document.readyState === 'loading') {
    await new Promise(resolve => document.addEventListener('DOMContentLoaded', resolve));
}

try {
    const resp = await PluginAPI.fetch(pluginId, '/public-config');
    const cfg = await resp.json();
    if (cfg.configured) {
        const target =
            document.querySelector('#pinScreen') ||
            document.querySelector('.login-screen') ||
            document.querySelector('.pin-screen');

        if (target && !document.getElementById('sso-login-btn')) {
            const btn = document.createElement('button');
            btn.id = 'sso-login-btn';
            btn.className = 'btn';
            btn.style.cssText = 'width:100%;margin-top:16px;display:flex;align-items:center;justify-content:center;gap:8px;';
            btn.innerHTML = '🔐 ' + (cfg.button_text || 'Mit SSO anmelden');
            btn.onclick = function () {
                globalThis.location.href = '/api/plugin/' + pluginId + '/login';
            };
            target.appendChild(btn);
        }
    }
} catch (e) {
    console.error('[sso] Login-Button konnte nicht eingefuegt werden:', e);
}

PluginAPI.addMenuItem('SSO', '🔐', async function () {
    const m = document.createElement('div');
    m.className = 'modal';
    m.style.display = 'flex';
    m.innerHTML =
        '<div class="modal-content" style="max-width:480px;width:95vw">' +
        '<h3>🔐 SSO Einstellungen</h3>' +
        '<p style="color:#888;font-size:0.85em;margin-top:-6px">Funktioniert mit jedem OpenID-Connect-Provider ' +
        '(Authentik, Keycloak, Auth0, Microsoft Entra ID, ...).</p>' +
        '<div id="sso-status" style="margin-bottom:10px;color:#888;font-size:0.9em">Lade...</div>' +
        '<div style="display:flex;flex-direction:column;gap:10px">' +
        '<label>Issuer-URL<br><input id="sso-issuer" type="text" style="width:100%" ' +
        'placeholder="https://meine-provider-domain/anwendung"></label>' +
        '<button class="btn" id="sso-test" type="button" style="align-self:flex-start">Verbindung testen</button>' +
        '<div id="sso-test-result" style="font-size:0.85em"></div>' +
        '<label>Client-ID<br><input id="sso-client-id" type="text" style="width:100%"></label>' +
        '<label>Client-Secret<br><input id="sso-client-secret" type="password" style="width:100%" ' +
        'placeholder="leer lassen = unveraendert"></label>' +
        '<label>Button-Text<br><input id="sso-button-text" type="text" style="width:100%" ' +
        'placeholder="z.B. Mit Firmenname anmelden"></label>' +
        '<label style="display:flex;align-items:center;gap:6px">' +
        '<input id="sso-autocreate" type="checkbox"> Neue Benutzer automatisch anlegen</label>' +
        '</div>' +
        '<div style="margin-top:16px;display:flex;gap:8px">' +
        '<button class="btn" id="sso-save">Speichern</button>' +
        '<button class="btn" onclick="this.closest(\'.modal\').remove()">Schliessen</button>' +
        '</div></div>';
    document.body.appendChild(m);
    m.addEventListener('click', function (e) { if (e.target === m) m.remove(); });

    const statusEl = document.getElementById('sso-status');
    const testResultEl = document.getElementById('sso-test-result');

    try {
        const resp = await PluginAPI.fetch(pluginId, '/config');
        if (resp.status === 403) {
            statusEl.textContent = 'Nur fuer Administratoren sichtbar.';
            return;
        }
        const cfg = await resp.json();
        document.getElementById('sso-issuer').value = cfg.issuer || '';
        document.getElementById('sso-client-id').value = cfg.client_id || '';
        document.getElementById('sso-client-secret').placeholder = cfg.client_secret
            ? 'gesetzt - leer lassen = unveraendert'
            : 'noch nicht gesetzt';
        document.getElementById('sso-button-text').value = cfg.button_text || '';
        document.getElementById('sso-autocreate').checked = !!cfg.autocreate;
        statusEl.textContent = '';
    } catch (e) {
        statusEl.textContent = 'Fehler beim Laden: ' + e.message;
    }

    document.getElementById('sso-test').onclick = async function () {
        const issuer = document.getElementById('sso-issuer').value.trim();
        testResultEl.textContent = 'Teste...';
        testResultEl.style.color = '#888';
        try {
            const resp = await PluginAPI.fetch(pluginId, '/test-issuer', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ issuer: issuer }),
            });
            const result = await resp.json();
            if (result.ok) {
                testResultEl.textContent = '✅ Provider erreichbar, Discovery erfolgreich';
                testResultEl.style.color = '#4caf50';
            } else {
                testResultEl.textContent = '❌ ' + (result.error || 'Unbekannter Fehler');
                testResultEl.style.color = '#e53935';
            }
        } catch (e) {
            testResultEl.textContent = '❌ ' + e.message;
            testResultEl.style.color = '#e53935';
        }
    };

    document.getElementById('sso-save').onclick = async function () {
        const body = {
            issuer: document.getElementById('sso-issuer').value.trim(),
            client_id: document.getElementById('sso-client-id').value.trim(),
            button_text: document.getElementById('sso-button-text').value.trim(),
            autocreate: document.getElementById('sso-autocreate').checked,
        };
        const secret = document.getElementById('sso-client-secret').value;
        if (secret) body.client_secret = secret;

        try {
            const resp = await PluginAPI.fetch(pluginId, '/config', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(body),
            });
            if (!resp.ok) throw new Error('HTTP ' + resp.status);
            showToast?.('✅ Gespeichert');
            m.remove();
        } catch (e) {
            showToast?.('❌ Fehler: ' + e.message, 'error');
        }
    };
});
