PluginAPI.addMenuItem('Preis-Aktualisierer', '🔄', function() {
    openPriceUpdaterModal();
});


async function openPriceUpdaterModal() {
    const m = document.createElement('div');
    m.className = 'modal';
    m.style.display = 'flex';
    m.innerHTML = `
        <div class="modal-content" style="max-width:700px;width:95vw;max-height:90vh;overflow-y:auto">
            <h3>🔄 Preis-Aktualisierer</h3>
            <p style="opacity:0.8;margin-bottom:15px">Verwalte URLs für automatische EK-Preis-Updates.</p>
            
            <div id="pu-content">
                <div style="text-align:center;padding:20px">Lade...</div>
            </div>
            
            <div style="margin-top:20px;padding-top:15px;border-top:1px solid rgba(255,255,255,0.2)">
                <button class="btn" id="pu-add-url" style="background:#4caf50">➕ Neue URL hinzufügen</button>
                <button class="btn" id="pu-update-all" style="background:#2196f3;margin-left:10px">🔄 Alle Preise aktualisieren</button>
                <button class="btn" onclick="this.closest('.modal').remove()" style="float:right">Schließen</button>
            </div>
        </div>
    `;
    document.body.appendChild(m);
    m.addEventListener('click', e => { if (e.target === m) m.remove(); });
    
    loadUrls();
    
    m.querySelector('#pu-add-url').addEventListener('click', () => openAddUrlModal());
    m.querySelector('#pu-update-all').addEventListener('click', (e) => updateAllPrices(e.target));
}


async function loadUrls() {
    const content = document.getElementById('pu-content');
    content.innerHTML = '<div style="text-align:center;padding:20px">Lade...</div>';
    
    try {
        const resp = await PluginAPI.fetch(pluginId, '/urls');
        if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
        const data = await resp.json();
        
        if (data.urls.length === 0) {
            content.innerHTML = `
                <div style="text-align:center;padding:30px;opacity:0.7">
                    <div style="font-size:3em;margin-bottom:10px">📭</div>
                    <p>Noch keine URLs konfiguriert.</p>
                    <p>Klicke auf "Neue URL hinzufügen" um zu starten.</p>
                </div>
            `;
            return;
        }
        
        let html = '<div style="display:grid;gap:10px">';
        data.urls.forEach(u => {
            html += `
                <div style="background:rgba(255,255,255,0.1);padding:12px;border-radius:8px;display:flex;align-items:center;gap:10px">
                    <div style="flex:1;min-width:0">
                        <div style="font-weight:600">${escapeHtml(u.name || 'Unbekannt')}</div>
                        <div style="font-size:0.85em;opacity:0.7;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${escapeHtml(u.url)}</div>
                        <div style="font-size:0.8em;opacity:0.6">Aktueller EK: ${u.ek || '—'}€</div>
                    </div>
                    <button class="btn pu-update-btn" data-url-id="${u.id}" data-product-id="${u.product_id}" style="background:#2196f3;padding:8px 12px;font-size:0.9em">🔄</button>
                    <button class="btn pu-delete-btn" data-url-id="${u.id}" style="background:#f44336;padding:8px 12px;font-size:0.9em">🗑️</button>
                </div>
            `;
        });
        html += '</div>';
        content.innerHTML = html;
        
        content.querySelectorAll('.pu-update-btn').forEach(btn => {
            btn.addEventListener('click', (e) => updateSinglePrice(e.target));
        });
        content.querySelectorAll('.pu-delete-btn').forEach(btn => {
            btn.addEventListener('click', (e) => deleteUrl(e.target.dataset.urlId));
        });
        
    } catch (e) {
        content.innerHTML = `<div style="text-align:center;padding:20px;color:#f44336">Fehler: ${e.message}</div>`;
        showToast?.('❌ URLs konnten nicht geladen werden', 'error');
    }
}


function openAddUrlModal() {
    const m = document.createElement('div');
    m.className = 'modal';
    m.style.display = 'flex';
    m.innerHTML = `
        <div class="modal-content" style="max-width:500px;width:95vw">
            <h3>➕ Neue URL hinzufügen</h3>
            
            <label style="display:block;margin-bottom:5px;font-weight:600">Produkt-ID</label>
            <input id="pu-product-id" type="number" style="width:100%;margin-bottom:15px;padding:10px;border-radius:8px;border:1px solid rgba(255,255,255,0.3);background:rgba(255,255,255,0.1);color:#fff" placeholder="z.B. 123">
            
            <label style="display:block;margin-bottom:5px;font-weight:600">URL</label>
            <input id="pu-url" type="url" style="width:100%;margin-bottom:15px;padding:10px;border-radius:8px;border:1px solid rgba(255,255,255,0.3);background:rgba(255,255,255,0.1);color:#fff" placeholder="https://...">
            
            <label style="display:block;margin-bottom:5px;font-weight:600">CSS-Selektor (optional)</label>
            <input id="pu-selector" type="text" style="width:100%;margin-bottom:15px;padding:10px;border-radius:8px;border:1px solid rgba(255,255,255,0.3);background:rgba(255,255,255,0.1);color:#fff" placeholder=".price oder #priceblock_ourprice">
            <div style="font-size:0.8em;opacity:0.7;margin-bottom:15px">Wenn leer, werden automatische Selektoren verwendet</div>
            
            <button class="btn" id="pu-save" style="background:#4caf50">💾 Speichern</button>
            <button class="btn" onclick="this.closest('.modal').remove()" style="float:right">Abbrechen</button>
        </div>
    `;
    document.body.appendChild(m);
    m.addEventListener('click', e => { if (e.target === m) m.remove(); });
    
    m.querySelector('#pu-save').addEventListener('click', async () => {
        const productId = parseInt(document.getElementById('pu-product-id').value);
        const url = document.getElementById('pu-url').value.trim();
        const selector = document.getElementById('pu-selector').value.trim();
        
        if (!productId || !url) {
            showToast?.('❌ Produkt-ID und URL sind erforderlich', 'error');
            return;
        }
        
        try {
            const resp = await PluginAPI.fetch(pluginId, '/urls', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ product_id: productId, url, selector }),
            });
            if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
            
            m.remove();
            loadUrls();
            showToast?.('✅ URL hinzugefügt');
        } catch (e) {
            showToast?.('❌ Fehler: ' + e.message, 'error');
        }
    });
}


async function deleteUrl(urlId) {
    if (!confirm('URL wirklich löschen?')) return;
    
    try {
        const resp = await PluginAPI.fetch(pluginId, `/urls/${urlId}`, { method: 'DELETE' });
        if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
        
        loadUrls();
        showToast?.('✅ URL gelöscht');
    } catch (e) {
        showToast?.('❌ Fehler: ' + e.message, 'error');
    }
}


async function updateSinglePrice(btn) {
    const productId = btn.dataset.productId;
    const originalText = btn.textContent;
    btn.textContent = '⏳';
    btn.disabled = true;
    
    try {
        const resp = await PluginAPI.fetch(pluginId, `/update/${productId}`, { method: 'POST' });
        if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
        const data = await resp.json();
        
        showToast?.(`✅ Preis aktualisiert: ${data.new_price}€`);
        loadUrls();
    } catch (e) {
        showToast?.('❌ Fehler: ' + e.message, 'error');
    } finally {
        btn.textContent = originalText;
        btn.disabled = false;
    }
}


async function updateAllPrices(btn) {
    if (!confirm('Alle Preise wirklich aktualisieren?')) return;
    
    const originalText = btn.textContent;
    btn.textContent = '⏳';
    btn.disabled = true;
    
    try {
        const resp = await PluginAPI.fetch(pluginId, '/update-all', { method: 'POST' });
        if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
        const data = await resp.json();
        
        showToast?.(`✅ ${data.summary.success} aktualisiert, ${data.summary.error} fehlerhaft`);
        loadUrls();
    } catch (e) {
        showToast?.('❌ Fehler: ' + e.message, 'error');
    } finally {
        btn.textContent = originalText;
        btn.disabled = false;
    }
}


function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
