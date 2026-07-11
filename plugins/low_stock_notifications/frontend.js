
(function() {
  'use strict';

  const pluginId = 'low_stock_notifications';
  let _settings = null;

  PluginAPI.addMenuItem('Benachrichtigungen', '🔔', function() {
    openNotifySettings();
  });

  function openNotifySettings() {
    const id = 'notifySettingsModal';
    let m = document.getElementById(id);
    if (m) { m.remove(); }

    m = document.createElement('div');
    m.id = id;
    m.className = 'modal';
    m.style.display = 'flex';
    m.innerHTML = `
      <div class="modal-content" style="max-width:700px;width:95vw;max-height:90vh;overflow-y:auto">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px">
          <h3 style="margin:0">🔔 Lager-Benachrichtigungen</h3>
          <button class="btn" onclick="_notifyCloseModal()" style="padding:6px 12px">✕</button>
        </div>

        <div id="notifyLoading" style="text-align:center;padding:40px;opacity:0.6">⏳ Lade Einstellungen...</div>

        <div id="notifyContent" style="display:none">
          <!-- Aktivieren -->
          <div style="margin-bottom:20px;padding:14px;background:rgba(255,255,255,0.05);border-radius:12px">
            <label style="display:flex;align-items:center;gap:12px;cursor:pointer">
              <input type="checkbox" id="notifyEnabled" onchange="_notifySave()" style="width:20px;height:20px">
              <span style="font-weight:600">Benachrichtigungen aktivieren</span>
            </label>
            <div style="margin-top:10px;font-size:0.85em;opacity:0.6">
              Prüft automatisch den Lagerbestand und benachrichtigt bei Unterdeckung.
            </div>
          </div>

          <!-- Check-Intervall -->
          <div style="margin-bottom:20px">
            <label style="display:block;margin-bottom:6px;font-weight:600;font-size:0.9em">Prüfintervall (Sekunden)</label>
            <input type="number" id="notifyInterval" value="60" min="30" max="3600" style="width:120px;padding:8px;border-radius:8px" onchange="_notifySave()">
            <span style="font-size:0.8em;opacity:0.5;margin-left:8px">Min: 30, Max: 3600</span>
          </div>

          <!-- Benachrichtigungstypen -->
          <div style="margin-bottom:20px;padding:14px;background:rgba(255,255,255,0.05);border-radius:12px">
            <div style="font-weight:600;margin-bottom:12px;font-size:0.95em">📋 Benachrichtigungstypen</div>
            <div style="display:grid;gap:8px">
              <label style="display:flex;align-items:center;gap:10px;cursor:pointer">
                <input type="checkbox" id="notifyLowStock" onchange="_notifySave()" style="width:18px;height:18px">
                <span>📦 Niedriger Lagerbestand</span>
              </label>
              <label style="display:flex;align-items:center;gap:10px;cursor:pointer">
                <input type="checkbox" id="notifyStockChange" onchange="_notifySave()" style="width:18px;height:18px">
                <span>📊 Bestandsänderungen</span>
              </label>
              <label style="display:flex;align-items:center;gap:10px;cursor:pointer">
                <input type="checkbox" id="notifyLogin" onchange="_notifySave()" style="width:18px;height:18px">
                <span>🔐 Geräte-Anmeldungen</span>
              </label>
              <label style="display:flex;align-items:center;gap:10px;cursor:pointer">
                <input type="checkbox" id="notifyIpChange" onchange="_notifySave()" style="width:18px;height:18px">
                <span>🌐 IP-Adress-Änderungen</span>
              </label>
              <label style="display:flex;align-items:center;gap:10px;cursor:pointer">
                <input type="checkbox" id="notifyNewTrustedDevice" onchange="_notifySave()" style="width:18px;height:18px">
                <span>✅ Neues vertrauenswürdiges Gerät/IP (automatisch)</span>
              </label>
              <label style="display:flex;align-items:center;gap:10px;cursor:pointer">
                <input type="checkbox" id="notifyNewTrustedDeviceManual" onchange="_notifySave()" style="width:18px;height:18px">
                <span>📝 Neues vertrauenswürdiges Gerät/IP (manuell)</span>
              </label>
              <label style="display:flex;align-items:center;gap:10px;cursor:pointer">
                <input type="checkbox" id="notifyPinChange" onchange="_notifySave()" style="width:18px;height:18px">
                <span>🔑 PIN-Änderungen</span>
              </label>
            </div>
          </div>

          <div style="margin-bottom:20px;padding:14px;background:rgba(255,255,255,0.05);border-radius:12px">
            <div style="font-weight:600;margin-bottom:12px;font-size:0.95em">👤 Benutzer-Filter (optional)</div>
            <div style="display:flex;flex-direction:column;gap:8px">
              <div style="display:flex;gap:8px;align-items:center;flex-wrap:wrap">
                <button class="btn" onclick="_notifyLoadUsers()" style="padding:8px 12px;font-size:0.85em">👥 Benutzer laden</button>
                <label style="display:flex;align-items:center;gap:10px;cursor:pointer;opacity:0.95">
                  <input type="checkbox" id="notifyUserFilterEnabled" onchange="_notifyToggleUserFilter(); _notifySaveAll()" style="width:18px;height:18px">
                  <span>Nur bestimmter Benutzer</span>
                </label>
              </div>
              <select id="notifyUsernameSelect" onchange="_notifySaveAll()" style="width:100%;padding:10px;border-radius:8px;border:1px solid rgba(255,255,255,0.2);background:rgba(0,0,0,0.25);color:#fff">
                <option value="">Alle Benutzer</option>
              </select>
              <div style="opacity:0.8;font-size:0.85em">Wenn deaktiviert: alle Benutzer. Wenn aktiviert: Auswahl aus Dropdown.</div>
            </div>
          </div>

          <!-- Tabs für Provider -->
          <div style="display:flex;gap:4px;margin-bottom:16px;flex-wrap:wrap">
            <button class="btn _notifyTab" data-tab="telegram" onclick="_notifySwitchTab('telegram')" style="padding:8px 14px;font-size:0.9em">📱 Telegram</button>
            <button class="btn _notifyTab" data-tab="discord" onclick="_notifySwitchTab('discord')" style="padding:8px 14px;font-size:0.9em">💬 Discord</button>
            <button class="btn _notifyTab" data-tab="webhook" onclick="_notifySwitchTab('webhook')" style="padding:8px 14px;font-size:0.9em">🔗 Webhook</button>
            <button class="btn _notifyTab" data-tab="email" onclick="_notifySwitchTab('email')" style="padding:8px 14px;font-size:0.9em">📧 E-Mail</button>
          </div>

          <!-- Telegram Tab -->
          <div id="notifyTabTelegram" class="_notifyTabContent" style="display:none">
            <div style="margin-bottom:14px">
              <label style="display:flex;align-items:center;gap:10px;margin-bottom:12px;cursor:pointer">
                <input type="checkbox" id="telegramEnabled" onchange="_notifySave()" style="width:18px;height:18px">
                <span>Telegram aktivieren</span>
              </label>
            </div>
            <div style="margin-bottom:14px">
              <label style="display:block;margin-bottom:6px;font-size:0.9em">Bot Token</label>
              <input type="text" id="telegramToken" placeholder="123456:ABC-DEF..." style="width:100%;padding:10px;border-radius:8px;font-family:monospace;font-size:0.9em">
              <div style="font-size:0.75em;opacity:0.5;margin-top:4px">Von @BotFather erhalten</div>
            </div>
            <div style="margin-bottom:14px">
              <label style="display:block;margin-bottom:6px;font-size:0.9em">Chat ID</label>
              <input type="text" id="telegramChatId" placeholder="-1001234567890" style="width:100%;padding:10px;border-radius:8px;font-family:monospace;font-size:0.9em">
              <div style="font-size:0.75em;opacity:0.5;margin-top:4px">Deine Chat-ID oder Gruppen-ID</div>
            </div>
            <button class="btn" onclick="_notifyTest('telegram')" style="background:rgba(74,144,226,0.2)">🧪 Testen</button>
            
            <!-- Telegram Anfragen -->
            <div id="telegramRequestsSection" style="margin-top:16px;padding-top:16px;border-top:1px solid rgba(255,255,255,0.1)">
              <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px">
                <span style="font-weight:600;font-size:0.9em">📥 Ausstehende Anfragen</span>
                <button class="btn" onclick="_notifyRefreshTelegramRequests()" style="padding:4px 8px;font-size:0.8em">🔄</button>
              </div>
              <div id="telegramRequestsList" style="max-height:150px;overflow-y:auto">
                <div style="opacity:0.5;padding:8px;font-size:0.85em">Lade...</div>
              </div>
              <div style="font-size:0.75em;opacity:0.5;margin-top:8px">
                Sende <code>/start</code> an deinen Bot um eine Anfrage zu stellen
              </div>
            </div>
          </div>

          <!-- Discord Tab -->
          <div id="notifyTabDiscord" class="_notifyTabContent" style="display:none">
            <div style="margin-bottom:14px">
              <label style="display:flex;align-items:center;gap:10px;margin-bottom:12px;cursor:pointer">
                <input type="checkbox" id="discordEnabled" onchange="_notifySave()" style="width:18px;height:18px">
                <span>Discord aktivieren</span>
              </label>
            </div>
            <div style="margin-bottom:14px">
              <label style="display:block;margin-bottom:6px;font-size:0.9em">Webhook URL</label>
              <input type="text" id="discordWebhook" placeholder="https://discord.com/api/webhooks/..." style="width:100%;padding:10px;border-radius:8px;font-family:monospace;font-size:0.85em">
              <div style="font-size:0.75em;opacity:0.5;margin-top:4px">In Discord: Kanal bearbeiten → Integrationen → Webhooks</div>
            </div>
            <button class="btn" onclick="_notifyTest('discord')" style="background:rgba(88,101,242,0.2)">🧪 Testen</button>
          </div>

          <!-- Webhook Tab -->
          <div id="notifyTabWebhook" class="_notifyTabContent" style="display:none">
            <div style="margin-bottom:14px">
              <label style="display:flex;align-items:center;gap:10px;margin-bottom:12px;cursor:pointer">
                <input type="checkbox" id="webhookEnabled" onchange="_notifySave()" style="width:18px;height:18px">
                <span>Webhook aktivieren</span>
              </label>
            </div>
            <div style="margin-bottom:14px">
              <label style="display:block;margin-bottom:6px;font-size:0.9em">Webhook URL</label>
              <input type="text" id="webhookUrl" placeholder="https://dein-server.com/webhook" style="width:100%;padding:10px;border-radius:8px;font-family:monospace;font-size:0.85em">
              <div style="font-size:0.75em;opacity:0.5;margin-top:4px">Sendet JSON-POST mit Low-Stock-Daten</div>
            </div>
            <button class="btn" onclick="_notifyTest('webhook')" style="background:rgba(255,255,255,0.1)">🧪 Testen</button>
          </div>

          <!-- E-Mail Tab -->
          <div id="notifyTabEmail" class="_notifyTabContent" style="display:none">
            <div style="margin-bottom:14px">
              <label style="display:flex;align-items:center;gap:10px;margin-bottom:12px;cursor:pointer">
                <input type="checkbox" id="emailEnabled" onchange="_notifySave()" style="width:18px;height:18px">
                <span>E-Mail aktivieren</span>
              </label>
            </div>
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:14px">
              <div>
                <label style="display:block;margin-bottom:6px;font-size:0.9em">SMTP Server</label>
                <input type="text" id="emailSmtp" placeholder="smtp.gmail.com" style="width:100%;padding:10px;border-radius:8px">
              </div>
              <div>
                <label style="display:block;margin-bottom:6px;font-size:0.9em">Port</label>
                <input type="number" id="emailPort" value="587" style="width:100%;padding:10px;border-radius:8px">
              </div>
            </div>
            <div style="margin-bottom:14px">
              <label style="display:block;margin-bottom:6px;font-size:0.9em">Benutzername</label>
              <input type="text" id="emailUser" placeholder="deine@email.de" style="width:100%;padding:10px;border-radius:8px">
            </div>
            <div style="margin-bottom:14px">
              <label style="display:block;margin-bottom:6px;font-size:0.9em">Passwort</label>
              <input type="password" id="emailPass" placeholder="App-Passwort" style="width:100%;padding:10px;border-radius:8px">
              <div style="font-size:0.75em;opacity:0.5;margin-top:4px">Für Gmail: App-Passwort verwenden</div>
            </div>
            <div style="margin-bottom:14px">
              <label style="display:block;margin-bottom:6px;font-size:0.9em">Empfänger</label>
              <input type="text" id="emailTo" placeholder="empfaenger@email.de" style="width:100%;padding:10px;border-radius:8px">
            </div>
            <div style="margin-bottom:14px">
              <label style="display:flex;align-items:center;gap:10px;cursor:pointer">
                <input type="checkbox" id="emailUseTls" checked style="width:18px;height:18px">
                <span>TLS verwenden (STARTTLS)</span>
              </label>
            </div>
            <button class="btn" onclick="_notifyTest('email')" style="background:rgba(255,193,7,0.2)">🧪 Testen</button>
          </div>

          <!-- Aktuelle niedrige Bestände -->
          <div style="margin-top:20px;padding-top:16px;border-top:1px solid rgba(255,255,255,0.1)">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px">
              <span style="font-weight:600">📦 Aktuell unter Mindestbestand</span>
              <button class="btn" onclick="_notifyRefreshLowStock()" style="padding:6px 12px;font-size:0.85em">🔄</button>
            </div>
            <div id="notifyLowStockList" style="max-height:200px;overflow-y:auto">
              <div style="opacity:0.5;padding:12px">Lade...</div>
            </div>
          </div>

          <div style="margin-top:20px;display:flex;gap:10px;justify-content:flex-end">
            <button class="btn" onclick="_notifyManualCheck()" style="background:rgba(255,255,255,0.1)">🔍 Jetzt prüfen</button>
            <button class="btn" onclick="_notifySaveAll()" style="background:#4a90e2;color:#fff">💾 Alle speichern</button>
          </div>
        </div>

        <div id="notifyTestResult" style="margin-top:12px;padding:10px;border-radius:8px;display:none"></div>
      </div>
    `;

    document.body.appendChild(m);
    m.addEventListener('click', function(e) { if (e.target === m) m.remove(); });

    _notifyLoadSettings();
    _notifySwitchTab('telegram');
  }

  window._notifyToggleUserFilter = function() {
    const enabled = document.getElementById('notifyUserFilterEnabled').checked;
    const sel = document.getElementById('notifyUsernameSelect');
    sel.disabled = !enabled;
    try {
      if (enabled && sel.options && sel.options.length <= 1) {
        _notifyLoadUsers();
      }
    } catch (e) {}
  };

  window._notifyLoadUsers = async function() {
    try {
      const resp = await fetch('/api/users', { credentials: 'include' });
      const data = await resp.json();
      let users = [];
      if (Array.isArray(data)) {
        users = data;
      } else if (data && Array.isArray(data.users)) {
        users = data.users;
      } else if (data && data.status === 'ok' && Array.isArray(data.data)) {
        users = data.data;
      }
      const names = [];
      for (const u of (users || [])) {
        if (typeof u === 'string') {
          if (u.trim()) names.push(u.trim());
        } else if (u && typeof u === 'object') {
          const n = (u.username || u.name || u.id || '').toString().trim();
          if (n) names.push(n);
        }
      }
      const sel = document.getElementById('notifyUsernameSelect');
      const current = sel.value;
      sel.innerHTML = '';
      const optAll = document.createElement('option');
      optAll.value = '';
      optAll.textContent = 'Alle Benutzer';
      sel.appendChild(optAll);
      for (const n of names) {
        const opt = document.createElement('option');
        opt.value = n;
        opt.textContent = n;
        sel.appendChild(opt);
      }
      sel.value = current;
      document.getElementById('notifyUsernameSelect').disabled = !document.getElementById('notifyUserFilterEnabled').checked;
    } catch (e) {
      console.error('[Notifications] Load users error:', e);
      if (typeof showToast === 'function') showToast('❌ Benutzer laden fehlgeschlagen');
    }
  };

  window._notifyCloseModal = async function() {
    try {
      await _notifySaveAll();
    } catch (e) {}
    const m = document.getElementById('notifySettingsModal');
    if (m) m.remove();
  };

  function _isMasked(v) {
    const s = String(v || '');
    if (!s) return true;
    if (s === '********') return true;
    if (s.indexOf('...') !== -1) return true;
    return false;
  }

  window._notifySwitchTab = function(tab) {
    document.querySelectorAll('._notifyTabContent').forEach(el => el.style.display = 'none');
    document.querySelectorAll('._notifyTab').forEach(el => el.style.opacity = '0.5');
    document.getElementById('notifyTab' + tab.charAt(0).toUpperCase() + tab.slice(1)).style.display = 'block';
    document.querySelector(`._notifyTab[data-tab="${tab}"]`).style.opacity = '1';
  };

  async function _notifyLoadSettings() {
    const loadingEl = document.getElementById('notifyLoading');
    const contentEl = document.getElementById('notifyContent');
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 10000);
    try {
      const resp = await PluginAPI.fetch(pluginId, '/settings', { signal: controller.signal });
      if (!resp || !resp.ok) {
        throw new Error('HTTP ' + (resp ? resp.status : '0'));
      }
      const data = await resp.json();
      if (!data || data.status !== 'ok') {
        throw new Error((data && data.message) ? data.message : 'Unbekannter Fehler');
      }
      _settings = data.settings;
      _notifyPopulateForm();
    } catch (e) {
      const msg = (e && e.name === 'AbortError') ? 'Timeout beim Laden der Einstellungen' : (e && e.message ? e.message : String(e));
      if (loadingEl) {
        loadingEl.style.display = 'block';
        loadingEl.innerHTML = '❌ Fehler beim Laden: ' + msg;
      }
      if (contentEl) {
        contentEl.style.display = 'none';
      }
    } finally {
      clearTimeout(timeoutId);
    }
  }

  function _notifyPopulateForm() {
    const s = _settings || {};
    document.getElementById('notifyEnabled').checked = s.enabled !== false;
    document.getElementById('notifyInterval').value = s.check_interval || 60;
    document.getElementById('notifyLowStock').checked = s.notify_low_stock !== false;
    document.getElementById('notifyStockChange').checked = s.notify_stock_change !== false;
    document.getElementById('notifyLogin').checked = s.notify_login !== false;
    document.getElementById('notifyIpChange').checked = s.notify_ip_change !== false;
    document.getElementById('notifyNewTrustedDevice').checked = s.notify_new_trusted_device !== false;
    document.getElementById('notifyNewTrustedDeviceManual').checked = s.notify_new_trusted_device_manual !== false;
    document.getElementById('notifyPinChange').checked = s.notify_pin_change !== false;
    const uf = (s.notify_username_filter || '').trim();
    document.getElementById('notifyUserFilterEnabled').checked = !!uf;
    document.getElementById('notifyUsernameSelect').value = uf;
    _notifyToggleUserFilter();
    document.getElementById('telegramEnabled').checked = s.telegram_enabled || false;
    document.getElementById('telegramToken').value = s.telegram_token_masked || '';
    document.getElementById('telegramChatId').value = s.telegram_chat_id || '';
    document.getElementById('discordEnabled').checked = s.discord_enabled || false;
    document.getElementById('discordWebhook').value = s.discord_webhook || '';
    document.getElementById('webhookEnabled').checked = s.webhook_enabled || false;
    document.getElementById('webhookUrl').value = s.webhook_url || '';
    document.getElementById('emailEnabled').checked = s.email_enabled || false;
    document.getElementById('emailSmtp').value = s.email_smtp || '';
    document.getElementById('emailPort').value = s.email_port || 587;
    document.getElementById('emailUser').value = s.email_user || '';
    document.getElementById('emailPass').value = s.email_pass_masked || '';
    document.getElementById('emailTo').value = s.email_to || '';
    document.getElementById('emailUseTls').checked = s.email_use_tls !== false;

    document.getElementById('notifyLoading').style.display = 'none';
    document.getElementById('notifyContent').style.display = 'block';

    _notifyRefreshLowStock();
    _notifyRefreshTelegramRequests();
  }

  window._notifyRefreshLowStock = async function() {
    const container = document.getElementById('notifyLowStockList');
    try {
      const resp = await PluginAPI.fetch(pluginId, '/low-stock');
      const data = await resp.json();
      if (data.status === 'ok') {
        if (data.low_stock.length === 0) {
          container.innerHTML = '<div style="opacity:0.5;padding:12px;text-align:center">✅ Alle Produkte haben ausreichend Bestand</div>';
        } else {
          container.innerHTML = data.low_stock.map(item => `
            <div style="display:flex;justify-content:space-between;align-items:center;padding:8px 12px;background:rgba(255,107,107,0.1);border-radius:8px;margin-bottom:6px">
              <span style="font-weight:600">${_nEsc(item.name)}</span>
              <span style="color:#ff6b6b;font-size:0.9em">${item.stock} / ${item.min_stock} Stk</span>
            </div>
          `).join('');
        }
      }
    } catch (e) {
      container.innerHTML = '<div style="color:#ff6b6b;padding:12px">Fehler: ' + e.message + '</div>';
    }
  };

  window._notifyTest = async function(type) {
    const result = document.getElementById('notifyTestResult');
    result.style.display = 'block';
    result.style.background = 'rgba(255,255,255,0.05)';
    result.innerHTML = '⏳ Sende Test...';

    const payload = { type: type };

    if (type === 'telegram') {
      const t = document.getElementById('telegramToken').value;
      if (!_isMasked(t)) payload.telegram_token = t;
      payload.telegram_chat_id = document.getElementById('telegramChatId').value;
    } else if (type === 'discord') {
      payload.discord_webhook = document.getElementById('discordWebhook').value;
    } else if (type === 'webhook') {
      payload.webhook_url = document.getElementById('webhookUrl').value;
    } else if (type === 'email') {
      payload.email_smtp = document.getElementById('emailSmtp').value;
      payload.email_port = parseInt(document.getElementById('emailPort').value) || 587;
      payload.email_user = document.getElementById('emailUser').value;
      payload.email_pass = document.getElementById('emailPass').value;
      payload.email_to = document.getElementById('emailTo').value;
      payload.email_use_tls = document.getElementById('emailUseTls').checked;
    }

    try {
      const resp = await PluginAPI.fetch(pluginId, '/test', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const data = await resp.json();

      if (data.status === 'ok') {
        result.style.background = 'rgba(46,213,115,0.15)';
        result.innerHTML = '✅ Test erfolgreich!';
      } else {
        result.style.background = 'rgba(255,107,107,0.15)';
        result.innerHTML = '❌ ' + _nEsc(data.message || 'Unbekannter Fehler');
      }
    } catch (e) {
      result.style.background = 'rgba(255,107,107,0.15)';
      result.innerHTML = '❌ Fehler: ' + _nEsc(e.message);
    }
  };

  window._notifySave = async function() {
    const settings = {
      enabled: document.getElementById('notifyEnabled').checked,
      check_interval: parseInt(document.getElementById('notifyInterval').value) || 60,
      telegram_enabled: document.getElementById('telegramEnabled').checked,
      discord_enabled: document.getElementById('discordEnabled').checked,
      webhook_enabled: document.getElementById('webhookEnabled').checked,
      email_enabled: document.getElementById('emailEnabled').checked
    };
    await _notifySaveToBackend(settings);
  };

  window._notifySaveAll = async function() {
    if (document.getElementById('notifyContent') && document.getElementById('notifyContent').style.display === 'none') {
      return;
    }
    const userFilterEnabled = document.getElementById('notifyUserFilterEnabled').checked;
    const selectedUser = document.getElementById('notifyUsernameSelect').value;
    const settings = {
      enabled: document.getElementById('notifyEnabled').checked,
      check_interval: parseInt(document.getElementById('notifyInterval').value) || 60,
      notify_username_filter: userFilterEnabled ? selectedUser : '',
      notify_low_stock: document.getElementById('notifyLowStock').checked,
      notify_stock_change: document.getElementById('notifyStockChange').checked,
      notify_login: document.getElementById('notifyLogin').checked,
      notify_ip_change: document.getElementById('notifyIpChange').checked,
      notify_new_trusted_device: document.getElementById('notifyNewTrustedDevice').checked,
      notify_new_trusted_device_manual: document.getElementById('notifyNewTrustedDeviceManual').checked,
      notify_pin_change: document.getElementById('notifyPinChange').checked,
      telegram_enabled: document.getElementById('telegramEnabled').checked,
      telegram_token: document.getElementById('telegramToken').value,
      telegram_chat_id: document.getElementById('telegramChatId').value,
      discord_enabled: document.getElementById('discordEnabled').checked,
      discord_webhook: document.getElementById('discordWebhook').value,
      webhook_enabled: document.getElementById('webhookEnabled').checked,
      webhook_url: document.getElementById('webhookUrl').value,
      email_enabled: document.getElementById('emailEnabled').checked,
      email_smtp: document.getElementById('emailSmtp').value,
      email_port: parseInt(document.getElementById('emailPort').value) || 587,
      email_user: document.getElementById('emailUser').value,
      email_pass: document.getElementById('emailPass').value,
      email_to: document.getElementById('emailTo').value,
      email_use_tls: document.getElementById('emailUseTls').checked
    };

    if (_isMasked(settings.telegram_token)) delete settings.telegram_token;
    if (_isMasked(settings.email_pass)) delete settings.email_pass;

    const ok = await _notifySaveToBackend(settings);
    if (ok && typeof showToast === 'function') {
      showToast('✅ Einstellungen gespeichert');
    }
  };

  async function _notifySaveToBackend(settings) {
    try {
      const resp = await PluginAPI.fetch(pluginId, '/settings', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(settings)
      });
      const data = await resp.json();
      return data.status === 'ok';
    } catch (e) {
      console.error('[Notifications] Save error:', e);
      return false;
    }
  }

  window._notifyManualCheck = async function() {
    try {
      const resp = await PluginAPI.fetch(pluginId, '/check', { method: 'POST' });
      const data = await resp.json();
      if (data.status === 'ok') {
        if (typeof showToast === 'function') showToast('✅ Prüfung durchgeführt');
        _notifyRefreshLowStock();
      }
    } catch (e) {
      console.error('[Notifications] Check error:', e);
    }
  };

  function _nEsc(str) {
    return String(str || '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  }

  window._notifyRefreshTelegramRequests = async function() {
    const container = document.getElementById('telegramRequestsList');
    if (!container) return;
    
    try {
      const resp = await PluginAPI.fetch(pluginId, '/telegram/requests');
      const data = await resp.json();
      
      if (data.status === 'ok') {
        if (!data.requests || data.requests.length === 0) {
          container.innerHTML = '<div style="opacity:0.5;padding:8px;font-size:0.85em;text-align:center">Keine ausstehenden Anfragen</div>';
        } else {
          container.innerHTML = data.requests.map(r => `
            <div style="display:flex;justify-content:space-between;align-items:center;padding:8px 10px;background:rgba(74,144,226,0.1);border-radius:8px;margin-bottom:6px">
              <div>
                <div style="font-weight:600">${_nEsc(r.username)}</div>
                <div style="font-size:0.75em;opacity:0.5">${r.chat_id}</div>
              </div>
              <div style="display:flex;gap:4px">
                <button class="btn" onclick="_notifyHandleTelegramRequest('${r.chat_id}', 'accept')" style="padding:4px 8px;font-size:0.8em;background:rgba(46,213,115,0.2)">✓</button>
                <button class="btn" onclick="_notifyHandleTelegramRequest('${r.chat_id}', 'reject')" style="padding:4px 8px;font-size:0.8em;background:rgba(255,107,107,0.2)">✕</button>
              </div>
            </div>
          `).join('');
        }
      }
    } catch (e) {
      container.innerHTML = '<div style="color:#ff6b6b;padding:8px;font-size:0.85em">Fehler: ' + e.message + '</div>';
    }
  };

  window._notifyHandleTelegramRequest = async function(chatId, action) {
    try {
      const resp = await PluginAPI.fetch(pluginId, '/telegram/requests/' + chatId, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action: action })
      });
      const data = await resp.json();
      
      if (data.status === 'ok') {
        if (typeof showToast === 'function') {
          showToast(action === 'accept' ? '✅ Anfrage akzeptiert' : '❌ Anfrage abgelehnt');
        }
        _notifyRefreshTelegramRequests();
        
        if (action === 'accept') {
          _notifyLoadSettings();
        }
      } else {
        alert('Fehler: ' + (data.message || 'Unbekannt'));
      }
    } catch (e) {
      alert('Fehler: ' + e.message);
    }
  };

})();