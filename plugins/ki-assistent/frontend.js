(function() {
  'use strict';

  const pluginId = 'ki-assistent';

  let _settings = null;
  let _chatHistory = [];
  let _chatSessions = [];
  let _isOpen = false;
  let _activeRequestController = null;
  let _activeRequestTimeoutId = null;
  let _activeLoadingId = null;

  function _createModal(id) {
    let m = document.getElementById(id);
    if (m) { m.remove(); }
    m = document.createElement('div');
    m.id = id;
    m.className = 'modal';
    m.style.display = 'flex';
    document.body.appendChild(m);
    m.addEventListener('click', function(e) { if (e.target === m) m.remove(); });
    return m;
  }

  function _removeModal(id) {
    const m = document.getElementById(id);
    if (m) m.remove();
  }

  function _kiEsc(str) {
    return String(str || '')
      .replaceAll('&', '&amp;')
      .replaceAll('<', '&lt;')
      .replaceAll('>', '&gt;')
      .replaceAll('"', '&quot;');
  }

  function _setLocalStorage(key, value) {
    try {
      localStorage.setItem(key, value);
    } catch(e) {
      console.warn('[KI] Could not save to localStorage:', e);
    }
  }

  function _getLocalStorage(key, defaultValue = null) {
    try {
      return localStorage.getItem(key) || defaultValue;
    } catch(e) {
      console.warn('[KI] Could not read from localStorage:', e);
      return defaultValue;
    }
  }

  function _getSettingsObject() {
    return {
      provider: document.querySelector('input[name="kiProvider"]:checked')?.value || 'ollama',
      ollama_url: document.getElementById('kiOllamaUrl')?.value || '',
      ollama_model: document.getElementById('kiOllamaModel')?.value || '',
      api_url: document.getElementById('kiApiUrl')?.value || '',
      api_key: document.getElementById('kiApiKey')?.value || '',
      api_model: document.getElementById('kiApiModel')?.value || '',
      timeout: Number.parseInt(document.getElementById('kiTimeout')?.value, 10) || 120,
      product_limit: Number.parseInt(document.getElementById('kiProductLimit')?.value, 10) || 50,
      system_instruction: document.getElementById('kiSystemInstruction')?.value || ''
    };
  }

  function _renderChatBubble(msg, isUser) {
    const bgColor = isUser ? 'background:#4a90e2;color:#fff' : 'background:rgba(255,255,255,0.08)';
    const justify = isUser ? 'flex-end' : 'flex-start';
    const radius = isUser ? '16px 16px 4px 16px' : '16px 16px 16px 4px';
    const lineHeight = isUser ? '' : ';line-height:1.5';
    
    return `<div style="display:flex;justify-content:${justify}">
      <div style="${bgColor};padding:10px 16px;border-radius:${radius};max-width:80%;white-space:pre-wrap${lineHeight}">${_kiEsc(msg)}</div>
    </div>`;
  }

  PluginAPI.addMenuItem('KI-Assistent', '🤖', function() {
    openKIChat();
  });

  function openKIChat() {
    const id = 'kiChatModal';
    const m = _createModal(id);

    m.innerHTML = `
      <div class="modal-content" style="max-width:800px;width:95vw;height:85vh;display:flex;flex-direction:column">
        <div style="display:flex;justify-content:space-between;align-items:center;padding:12px 16px;border-bottom:1px solid rgba(255,255,255,0.1)">
          <h3 style="margin:0;display:flex;align-items:center;gap:10px">
            <span></span>
            <span>KI Lagerassistent</span>
            <span id="kiStatusBadge" style="font-size:0.6em;padding:3px 8px;border-radius:10px;background:rgba(255,255,255,0.1)">⏳</span>
          </h3>
          <div style="display:flex;gap:8px;align-items:center">
            <div style="position:relative">
              <button id="kiHistoryBtn" class="btn" onclick="_kiToggleHistory()" style="padding:6px 10px;font-size:0.9em" title="Chat-Verlauf">🕐</button>
              <div id="kiHistoryDropdown" style="display:none;position:absolute;top:100%;right:0;background:#222;border:1px solid rgba(255,255,255,0.2);border-radius:8px;min-width:200px;max-height:300px;overflow-y:auto;z-index:1000;box-shadow:0 4px 12px rgba(0,0,0,0.3)"></div>
            </div>
            <button class="btn" onclick="_kiOpenSettings()" style="padding:6px 10px;font-size:0.9em" title="Einstellungen">⚙️</button>
            <button class="btn" onclick="_kiRequestClose()" style="padding:6px 12px">✕</button>
          </div>
        </div>
        <div id="kiChatMessages" style="flex:1;overflow-y:auto;padding:16px;display:flex;flex-direction:column;gap:12px">
          <div style="text-align:center;opacity:0.5;padding:40px 20px">
            <div style="font-size:2.5em;margin-bottom:12px">🤖</div>
            <div style="font-weight:600;margin-bottom:8px">KI Lagerassistent</div>
            <div style="font-size:0.9em;max-width:300px;margin:0 auto;line-height:1.6">
              Frage mich alles über dein Lager: Bestände, Lagerorte, Nachbestellungen...
            </div>
          </div>
        </div>
        <div style="padding:12px 16px;border-top:1px solid rgba(255,255,255,0.1)">
          <div style="display:flex;gap:10px;align-items:flex-end">
            <textarea id="kiInput" placeholder="Frage stellen..." style="flex:1;min-height:44px;max-height:120px;padding:10px 14px;border-radius:12px;resize:vertical;font-size:1em" rows="1"></textarea>
            <button id="kiSendBtn" class="btn" onclick="_kiSendMessage()" style="padding:10px 18px;font-weight:600">Senden</button>
          </div>
          <div style="font-size:0.75em;opacity:0.4;margin-top:8px">
            Enter zum Senden · Shift+Enter für neue Zeile
          </div>
        </div>
      </div>
    `;

    const input = document.getElementById('kiInput');
    const draft = _getLocalStorage('ki_chat_draft', '');
    if (draft) input.value = draft;

    input.addEventListener('keydown', function(e) {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        _kiSendMessage();
      }
    });
    input.addEventListener('input', function() {
      _setLocalStorage('ki_chat_draft', input.value || '');
    });

    _kiLoadSettings();
    _kiLoadSessions();
    _isOpen = true;
  }

  globalThis._kiOpenSettings = async function() {
    const id = 'kiSettingsModal';
    const m = _createModal(id);

    if (!_settings) {
      await _kiLoadSettings();
    }
    const s = _settings || {};

    m.innerHTML = `
      <div class="modal-content" style="max-width:550px;width:95vw;max-height:90vh;overflow-y:auto">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px">
          <h3 style="margin:0">⚙️ KI-Einstellungen</h3>
          <button class="btn" onclick="document.getElementById('kiSettingsModal').remove()" style="padding:6px 12px">✕</button>
        </div>

        <div style="margin-bottom:20px">
          <label style="display:flex;align-items:center;gap:10px;margin-bottom:12px;cursor:pointer">
            <input type="radio" name="kiProvider" value="ollama" ${s.provider === 'ollama' ? 'checked' : ''} onchange="_kiToggleProvider()">
            <span><strong>Ollama</strong> <span style="opacity:0.5;font-size:0.85em">(Lokal, kostenlos)</span></span>
          </label>
          <label style="display:flex;align-items:center;gap:10px;cursor:pointer">
            <input type="radio" name="kiProvider" value="api" ${s.provider === 'api' ? 'checked' : ''} onchange="_kiToggleProvider()">
            <span><strong>API</strong> <span style="opacity:0.5;font-size:0.85em">(OpenAI, LM Studio, etc.)</span></span>
          </label>
        </div>

        <div id="kiOllamaSettings" style="${s.provider === 'api' ? 'display:none' : ''}">
          <div style="margin-bottom:14px">
            <label style="display:block;margin-bottom:6px;font-weight:600;font-size:0.9em">Ollama URL</label>
            <input id="kiOllamaUrl" value="${s.ollama_url || 'http://localhost:11434'}" placeholder="http://localhost:11434" style="width:100%;padding:10px;border-radius:8px">
          </div>
          <div style="margin-bottom:14px">
            <label style="display:block;margin-bottom:6px;font-weight:600;font-size:0.9em">Modell</label>
            <div style="display:flex;gap:8px">
              <input id="kiOllamaModel" value="${s.ollama_model || 'llama3.2'}" placeholder="llama3.2" style="flex:1;padding:10px;border-radius:8px">
              <button class="btn" onclick="_kiLoadOllamaModels()" style="padding:10px 14px">🔄</button>
            </div>
            <div id="kiOllamaModels" style="margin-top:8px;font-size:0.85em;opacity:0.6"></div>
          </div>
        </div>

        <div id="kiApiSettings" style="${s.provider === 'api' ? 'display:block' : 'display:none'}">
          <div style="margin-bottom:14px">
            <label style="display:block;margin-bottom:6px;font-weight:600;font-size:0.9em">API URL</label>
            <input id="kiApiUrl" value="${s.api_url || 'https://api.openai.com/v1/chat/completions'}" placeholder="https://api.openai.com/v1/chat/completions" style="width:100%;padding:10px;border-radius:8px">
            <div style="font-size:0.75em;opacity:0.5;margin-top:4px">LM Studio: http://localhost:1234/v1/chat/completions</div>
          </div>
          <div style="margin-bottom:14px">
            <label style="display:block;margin-bottom:6px;font-weight:600;font-size:0.9em">API Key</label>
            <input id="kiApiKey" type="password" value="${s.api_key_masked || ''}" placeholder="sk-..." style="width:100%;padding:10px;border-radius:8px">
          </div>
          <div style="margin-bottom:14px">
            <label style="display:block;margin-bottom:6px;font-weight:600;font-size:0.9em">Modell</label>
            <input id="kiApiModel" value="${s.api_model || 'gpt-4o-mini'}" placeholder="gpt-4o-mini" style="width:100%;padding:10px;border-radius:8px">
          </div>
        </div>

        <div style="margin-bottom:20px;padding:14px;background:rgba(255,255,255,0.05);border-radius:12px">
          <label style="display:block;margin-bottom:8px;font-weight:600;font-size:0.9em">⏱️ Timeout (Sekunden)</label>
          <input id="kiTimeout" type="number" value="${s.timeout || 180}" min="30" max="6000" style="width:120px;padding:10px;border-radius:8px">
          <div style="font-size:0.75em;opacity:0.5;margin-top:4px">Maximale Wartezeit für KI-Antwort (30-6000)</div>
        </div>

        <div style="margin-bottom:20px;padding:14px;background:rgba(255,255,255,0.05);border-radius:12px">
          <label style="display:block;margin-bottom:8px;font-weight:600;font-size:0.9em">📦 Produkt-Abruf-Limit</label>
          <input id="kiProductLimit" type="number" value="${s.product_limit || 50}" min="5" max="500" style="width:120px;padding:10px;border-radius:8px">
          <div style="font-size:0.75em;opacity:0.5;margin-top:4px">Wie viele Produkte pro Anfrage als Kontext mitgeschickt werden (5-500)</div>
        </div>

        <div style="margin-bottom:20px;padding:14px;background:rgba(255,255,255,0.05);border-radius:12px">
          <label style="display:block;margin-bottom:8px;font-weight:600;font-size:0.9em">📝 System-Anweisung</label>
          <textarea id="kiSystemInstruction" placeholder="z.B. Bitte antworte immer auf Deutsch..." style="width:100%;padding:10px;border-radius:8px;min-height:60px;resize:vertical;font-size:0.9em">${s.system_instruction || ''}</textarea>
          <div style="font-size:0.75em;opacity:0.5;margin-top:4px">Zusätzliche Anweisung an die KI (wird bei jeder Nachricht mitgesendet)</div>
        </div>

        <div style="display:flex;gap:10px;justify-content:flex-end;margin-top:20px;padding-top:16px;border-top:1px solid rgba(255,255,255,0.1)">
          <button class="btn" onclick="_kiTestConnection()" style="background:rgba(255,255,255,0.1)">🔗 Verbindung testen</button>
          <button class="btn" onclick="_kiSaveSettings()" style="background:#4a90e2;color:#fff">💾 Speichern</button>
        </div>

        <div id="kiTestResult" style="margin-top:12px;padding:10px;border-radius:8px;display:none"></div>
      </div>
    `;
  };

  globalThis._kiToggleProvider = function() {
    const isApi = document.querySelector('input[name="kiProvider"]:checked').value === 'api';
    document.getElementById('kiOllamaSettings').style.display = isApi ? 'none' : 'block';
    document.getElementById('kiApiSettings').style.display = isApi ? 'block' : 'none';
  };

  globalThis._kiLoadOllamaModels = async function() {
    const container = document.getElementById('kiOllamaModels');
    container.innerHTML = '⏳ Lade Modelle...';

    try {
      const resp = await PluginAPI.fetch(pluginId, '/models');
      const data = await resp.json();

      if (data.status === 'ok' && data.models.length > 0) {
        container.innerHTML = 'Verfügbar: ' + data.models.map(m => `<code style="background:rgba(255,255,255,0.1);padding:2px 6px;border-radius:4px;cursor:pointer" onclick="document.getElementById('kiOllamaModel').value='${m}'">${m}</code>`).join(' ');
      } else {
        container.innerHTML = 'Keine Modelle gefunden. Ist Ollama gestartet?';
      }
    } catch (e) {
      container.innerHTML = 'Fehler: ' + e.message;
    }
  };

  globalThis._kiTestConnection = async function() {
    const result = document.getElementById('kiTestResult');
    result.style.display = 'block';
    result.style.background = 'rgba(255,255,255,0.05)';
    result.innerHTML = '⏳ Teste Verbindung...';

    const settings = _getSettingsObject();

    try {
      const resp = await PluginAPI.fetch(pluginId, '/test', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(settings)
      });
      const data = await resp.json();

      if (data.status === 'ok') {
        result.style.background = 'rgba(46,213,115,0.15)';
        result.innerHTML = '✅ Verbindung erfolgreich! Antwort: ' + (data.response || 'OK');
      } else {
        result.style.background = 'rgba(255,107,107,0.15)';
        result.innerHTML = '❌ ' + data.message;
      }
    } catch (e) {
      result.style.background = 'rgba(255,107,107,0.15)';
      result.innerHTML = '❌ Fehler: ' + e.message;
    }
  };

  globalThis._kiSaveSettings = async function() {
    const settings = _getSettingsObject();
    settings.enabled = true;

    try {
      const resp = await PluginAPI.fetch(pluginId, '/settings', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(settings)
      });
      const data = await resp.json();

      if (data.status === 'ok') {
        _settings = settings;
        if (typeof showToast === 'function') showToast('✅ KI-Einstellungen gespeichert');
        document.getElementById('kiSettingsModal')?.remove();
        _kiUpdateStatus();
      }
    } catch (e) {
      alert('Fehler beim Speichern: ' + e.message);
    }
  };

  async function _kiLoadSettings() {
    try {
      const resp = await PluginAPI.fetch(pluginId, '/settings');
      const data = await resp.json();
      if (data.status === 'ok') {
        _settings = data.settings;
        _kiUpdateStatus();
      }
    } catch (e) {
      console.error('[KI] Settings laden fehlgeschlagen:', e);
    }
  }

  function _kiUpdateStatus() {
    const badge = document.getElementById('kiStatusBadge');
    if (!badge) return;

    if (!_settings?.enabled) {
      badge.textContent = '⚠️ Nicht konfiguriert';
      badge.style.background = 'rgba(255,193,7,0.2)';
    } else if (_settings.provider === 'ollama') {
      badge.textContent = '🏠 Lokal';
      badge.style.background = 'rgba(46,213,115,0.2)';
    } else {
      badge.textContent = '🌐 API';
      badge.style.background = 'rgba(74,144,226,0.2)';
    }
  }

  function _kiRenderError(container, errorMsg) {
    container.innerHTML += `
      <div style="display:flex;justify-content:flex-start">
        <div style="background:rgba(255,107,107,0.15);padding:10px 16px;border-radius:16px 16px 16px 4px;max-width:80%">❌ ${_kiEsc(errorMsg)}</div>
      </div>
    `;
  }

  function _kiSetupAbortController(timeoutMs) {
    if (_activeRequestController) {
      try { _activeRequestController.abort(); } catch (e) {
        console.warn('[KI] Could not abort request:', e);
      }
    }
    const controller = new AbortController();
    _activeRequestController = controller;
    if (_activeRequestTimeoutId) {
      try { clearTimeout(_activeRequestTimeoutId); } catch (e) {
        console.warn('[KI] Could not clear timeout:', e);
      }
    }
    const timeoutId = setTimeout(() => controller.abort(), timeoutMs);
    _activeRequestTimeoutId = timeoutId;
    return { controller, timeoutId };
  }

  function _kiHandleApiResponse(container, data, msg) {
    if (data.status !== 'ok') {
      _kiRenderError(container, data.message || 'Unbekannter Fehler');
      return;
    }
    const response = data.response || '(Keine Antwort)';
    const isFirstMessage = _chatHistory.length === 0;
    _chatHistory.push({ role: 'user', content: msg }, { role: 'assistant', content: response });
    if (isFirstMessage) { _kiSaveSession(msg); }
    container.innerHTML += _renderChatBubble(response, false);
  }

  globalThis._kiSendMessage = async function() {
    const input = document.getElementById('kiInput');
    const msg = input.value.trim();
    if (!msg) return;

    input.value = '';
    input.style.height = '44px';

    const container = document.getElementById('kiChatMessages');
    if (!container) return;

    container.innerHTML += _renderChatBubble(msg, true);

    const loadingId = 'kiLoading_' + Date.now();
    _activeLoadingId = loadingId;
    container.innerHTML += `
      <div id="${loadingId}" style="display:flex;justify-content:flex-start">
        <div style="background:rgba(255,255,255,0.08);padding:10px 16px;border-radius:16px 16px 16px 4px;max-width:80%">
          <span style="opacity:0.6">⏳ Denkt nach...</span>
        </div>
      </div>
    `;
    container.scrollTop = container.scrollHeight;

    const timeoutMs = (_settings?.timeout || 180) * 1000;
    const { controller, timeoutId } = _kiSetupAbortController(timeoutMs);

    try {
      const resp = await PluginAPI.fetch(pluginId, '/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: msg, history: _chatHistory }),
        signal: controller.signal
      });
      clearTimeout(timeoutId);
      _activeRequestTimeoutId = null;
      const data = await resp.json();
      const loading = document.getElementById(loadingId);
      if (loading) loading.remove();
      _kiHandleApiResponse(container, data, msg);
    } catch (e) {
      clearTimeout(timeoutId);
      _activeRequestTimeoutId = null;
      const loading = document.getElementById(loadingId);
      if (loading) loading.remove();
      const errorMsg = e.name === 'AbortError'
        ? `Timeout nach ${timeoutMs / 1000}s - KI braucht länger. Erhöhe Timeout in Einstellungen.`
        : e.message;
      _kiRenderError(container, errorMsg);
    }

    _activeRequestController = null;
    _activeLoadingId = null;
    container.scrollTop = container.scrollHeight;
  };

  globalThis._kiRequestClose = function() {
    const modal = document.getElementById('kiChatModal');
    if (!modal) return;

    if (_activeRequestController) {
      const cid = 'kiCloseConfirm';
      const m = _createModal(cid);

      m.innerHTML = `
        <div class="modal-content" style="max-width:520px;width:95vw">
          <h3 style="margin:0 0 10px 0">Laufende Anfrage</h3>
          <div style="opacity:0.8;line-height:1.5;margin-bottom:14px">Es läuft gerade eine KI-Anfrage. Was soll passieren?</div>
          <div style="display:flex;gap:10px;justify-content:flex-end">
            <button class="btn" onclick="_kiCloseContinue()" style="background:rgba(255,255,255,0.1)">Weiterlaufen lassen</button>
            <button class="btn" onclick="_kiCloseStop()" style="background:rgba(255,107,107,0.2)">Stoppen</button>
          </div>
        </div>
      `;
      return;
    }

    modal.remove();
  };

  globalThis._kiCloseContinue = function() {
    _removeModal('kiCloseConfirm');
    _removeModal('kiChatModal');
  };

  globalThis._kiCloseStop = function() {
    try {
      if (_activeRequestTimeoutId) {
        clearTimeout(_activeRequestTimeoutId);
        _activeRequestTimeoutId = null;
      }
      if (_activeRequestController) {
        _activeRequestController.abort();
      }
    } catch (e) {
      console.warn('[KI] Could not stop request:', e);
    }
    _activeRequestController = null;
    const loading = _activeLoadingId ? document.getElementById(_activeLoadingId) : null;
    if (loading) loading.remove();
    _activeLoadingId = null;
    _removeModal('kiCloseConfirm');
    _removeModal('kiChatModal');
  };

  function _kiLoadSessions() {
    try {
      const stored = _getLocalStorage('ki_chat_sessions', '[]');
      _chatSessions = JSON.parse(stored);
    } catch(e) {
      console.error('[KI] Sessions laden fehlgeschlagen:', e);
      _chatSessions = [];
    }
  }

  function _kiSaveSession(firstMessage) {
    if (!firstMessage || _chatHistory.length < 2) return;
    
    const session = {
      id: Date.now(),
      title: firstMessage.substring(0, 50) + (firstMessage.length > 50 ? '...' : ''),
      date: new Date().toLocaleString('de-DE'),
      history: _chatHistory.slice()
    };
    
    _chatSessions.unshift(session);
    if (_chatSessions.length > 20) {
      _chatSessions = _chatSessions.slice(0, 20);
    }
    
    _setLocalStorage('ki_chat_sessions', JSON.stringify(_chatSessions));
  }

  globalThis._kiToggleHistory = function() {
    const dropdown = document.getElementById('kiHistoryDropdown');
    if (!dropdown) return;
    
    if (dropdown.style.display === 'block') {
      dropdown.style.display = 'none';
      return;
    }
    
    dropdown.style.display = 'block';
    
    if (_chatSessions.length === 0) {
      dropdown.innerHTML = '<div style="padding:12px;opacity:0.5;font-size:0.85em">Keine früheren Chats vorhanden</div>';
      return;
    }
    
    dropdown.innerHTML = _chatSessions.map((s, i) =>
      '<div style="display:flex;justify-content:space-between;gap:10px;align-items:center;padding:10px 12px;cursor:pointer;border-bottom:1px solid rgba(255,255,255,0.1);font-size:0.85em">' +
        '<div onclick="_kiLoadSession(' + i + ')" style="flex:1;min-width:0">' +
          '<div style="font-weight:600;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">' + _kiEsc(s.title) + '</div>' +
          '<div style="opacity:0.4;font-size:0.75em;margin-top:2px">' + s.date + '</div>' +
        '</div>' +
        '<div style="display:flex;gap:6px;flex:0 0 auto">' +
          '<button class="btn" onclick="event.stopPropagation();_kiRenameSession(' + i + ')" style="padding:4px 8px;font-size:0.8em;background:rgba(255,193,7,0.2)" title="Umbenennen">✏️</button>' +
          '<button class="btn" onclick="event.stopPropagation();_kiDeleteSession(' + i + ')" style="padding:4px 8px;font-size:0.8em;background:rgba(255,107,107,0.2)" title="Löschen">🗑️</button>' +
        '</div>' +
      '</div>'
    ).join('') + '<div onclick="_kiNewChat()" style="padding:10px 12px;cursor:pointer;font-size:0.85em;color:#4a90e2;text-align:center">+ Neuer Chat</div>';
  };

  function _updateHistoryDisplay() {
    _kiToggleHistory();
    _kiToggleHistory();
  }

  globalThis._kiRenameSession = function(index) {
    const session = _chatSessions[index];
    if (!session) return;
    const newTitle = prompt('Neuer Name für den Chat:', session.title || '');
    if (newTitle === null) return;
    session.title = String(newTitle).trim() || session.title;
    _setLocalStorage('ki_chat_sessions', JSON.stringify(_chatSessions));
    _updateHistoryDisplay();
  };

  globalThis._kiDeleteSession = function(index) {
    const session = _chatSessions[index];
    if (!session) return;
    const ok = confirm('Chat wirklich löschen?');
    if (!ok) return;
    _chatSessions.splice(index, 1);
    _setLocalStorage('ki_chat_sessions', JSON.stringify(_chatSessions));
    _updateHistoryDisplay();
  };

  globalThis._kiLoadSession = function(index) {
    const session = _chatSessions[index];
    if (!session) return;
    
    _chatHistory = session.history.slice();
    
    const container = document.getElementById('kiChatMessages');
    if (!container) return;
    
    container.innerHTML = '';
    session.history.forEach(msg => {
      container.innerHTML += _renderChatBubble(msg.content, msg.role === 'user');
    });
    
    document.getElementById('kiHistoryDropdown').style.display = 'none';
    container.scrollTop = container.scrollHeight;
  };

  globalThis._kiNewChat = function() {
    _chatHistory = [];
    const container = document.getElementById('kiChatMessages');
    if (container) {
      container.innerHTML = `
        <div style="text-align:center;opacity:0.5;padding:40px 20px">
          <div style="font-size:2.5em;margin-bottom:12px">🤖</div>
          <div style="font-weight:600;margin-bottom:8px">KI Lagerassistent</div>
          <div style="font-size:0.9em;max-width:300px;margin:0 auto;line-height:1.6">
            Frage mich alles über dein Lager: Bestände, Lagerorte, Nachbestellungen...
          </div>
        </div>
      `;
    }
    document.getElementById('kiHistoryDropdown').style.display = 'none';
  };

  document.addEventListener('input', function(e) {
    if (e.target.id === 'kiInput') {
      e.target.style.height = 'auto';
      e.target.style.height = Math.min(e.target.scrollHeight, 120) + 'px';
    }
  });

})();
