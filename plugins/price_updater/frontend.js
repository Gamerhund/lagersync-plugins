const pluginId = 'price_updater';

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
        u => {
                    const intervalLabels = {
                        manual: 'Manuell',
                        daily: 'Täglich',
                        weekly: 'Wöchentlich',
                        monthly: 'Monatlich'
                    };
                    const intervalLabel = intervalLabels[u.update_interval] || 'Manuell';

                    html += `
                        <div style="background:rgba(255,255,255,0.1);padding:12px;border-radius:8px;display:flex;align-items:center;gap:10px">
                            <div style="flex:1;min-width:0">
                                <div style="font-weight:600">${escapeHtml(u.name || 'Unbekannt')}</div>
                                <div style="font-size:0.85em;opacity:0.7;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${escapeHtml(u.url)}</div>
                                <div style="font-size:0.8em;opacity:0.6">Aktueller EK: ${u.ek || '—'}€ | Aktualisierung: ${intervalLabel}</div>
                            </div>
                            <button class="btn pu-update-btn" data-url-id="${u.id}" data-product-id="${u.product_id}" style="background:#2196f3;padding:8px 12px;font-size:0.9em">🔄</button>
                            <button class="btn pu-delete-btn" data-url-id="${u.id}" style="background:#f44336;padding:8px 12px;font-size:0.9em">🗑️</button>
                        </div>
                    `;
                }
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
            
            <label style="display:block;margin-bottom:5px;font-weight:600">Produkt suchen</label>
            <div style="display:flex;gap:10px;margin-bottom:15px">
                <input id="pu-product-search" type="text" style="flex:1;padding:10px;border-radius:8px;border:1px solid rgba(255,255,255,0.3);background:rgba(255,255,255,0.1);color:#fff" placeholder="🔍 Produktname oder SKU eingeben...">
                <button class="btn" id="pu-search-btn" style="background:#2196f3;padding:10px 15px">🔍</button>
            </div>
            
            <div id="pu-product-results" style="max-height:200px;overflow-y:auto;margin-bottom:15px;display:none"></div>
            
            <label style="display:block;margin-bottom:5px;font-weight:600">Ausgewähltes Produkt</label>
            <input id="pu-product-name" type="text" style="width:100%;margin-bottom:5px;padding:10px;border-radius:8px;border:1px solid rgba(255,255,255,0.3);background:rgba(255,255,255,0.1);color:#fff" placeholder="Kein Produkt ausgewählt" readonly>
            <input id="pu-product-id" type="hidden" value="">
            
            <label style="display:block;margin-bottom:5px;font-weight:600">URL</label>
            <input id="pu-url" type="url" style="width:100%;margin-bottom:15px;padding:10px;border-radius:8px;border:1px solid rgba(255,255,255,0.3);background:rgba(255,255,255,0.1);color:#fff" placeholder="https://...">
            
            <label style="display:block;margin-bottom:5px;font-weight:600">CSS-Selektor (optional)</label>
            <input id="pu-selector" type="text" style="width:100%;margin-bottom:15px;padding:10px;border-radius:8px;border:1px solid rgba(255,255,255,0.3);background:rgba(255,255,255,0.1);color:#fff" placeholder=".price oder #priceblock_ourprice">
            <div style="font-size:0.8em;opacity:0.7;margin-bottom:15px">Wenn leer, werden automatische Selektoren verwendet</div>
            
            <label style="display:block;margin-bottom:5px;font-weight:600">Automatische Aktualisierung</label>
            <select id="pu-interval" style="width:100%;margin-bottom:15px;padding:10px;border-radius:8px;border:1px solid rgba(255,255,255,0.3);background:rgba(255,255,255,0.1);color:#fff">
                <option value="manual">Manuell (nur auf Knopfdruck)</option>
                <option value="daily">Täglich</option>
                <option value="weekly">Wöchentlich</option>
                <option value="monthly">Monatlich</option>
            </select>
            
            <button class="btn" id="pu-save" style="background:#4caf50">💾 Speichern</button>
            <button class="btn" onclick="this.closest('.modal').remove()" style="float:right">Abbrechen</button>
        </div>
    `;
    document.body.appendChild(m);
    m.addEventListener('click', e => { if (e.target === m) m.remove(); });
    
    const searchInput = m.querySelector('#pu-product-search');
    const searchBtn = m.querySelector('#pu-search-btn');
    const resultsDiv = m.querySelector('#pu-product-results');
    const productNameInput = m.querySelector('#pu-product-name');
    const productIdInput = m.querySelector('#pu-product-id');
    
    async function searchProducts() {
        const query = searchInput.value.trim();
        if (!query || query.length < 2) {
            resultsDiv.style.display = 'none';
            return;
        }
        
        resultsDiv.innerHTML = '<div style="text-align:center;padding:10px">Suche...</div>';
        resultsDiv.style.display = 'block';
        
        try {
            const resp = await PluginAPI.fetch(pluginId, `/search-products?q=${encodeURIComponent(query)}`);
            if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
            const data = await resp.json();
            
            if (data.products.length === 0) {
                resultsDiv.innerHTML = '<div style="text-align:center;padding:10px;opacity:0.7">Keine Produkte gefunden</div>';
                return;
            }
            
            let html = '<div style="display:flex;flex-direction:column;gap:5px">';
            data.products.forEach(p => {
                html += `
                    <div class="pu-product-option" data-id="${p.id}" data-name="${escapeHtml(p.name)}" style="padding:10px;background:rgba(255,255,255,0.1);border-radius:6px;cursor:pointer;display:flex;justify-content:space-between;align-items:center">
                        <div>
                            <div style="font-weight:600">${escapeHtml(p.name)}</div>
                            <div style="font-size:0.8em;opacity:0.7">ID: ${p.id} ${p.sku ? '| SKU: ' + escapeHtml(p.sku) : ''} | EK: ${p.ek || '—'}€</div>
                        </div>
                        <span style="color:#4caf50">➕</span>
                    </div>
                `;
            });
            html += '</div>';
            resultsDiv.innerHTML = html;
            
            resultsDiv.querySelectorAll('.pu-product-option').forEach(opt => {
                opt.addEventListener('click', () => {
                    productIdInput.value = opt.dataset.id;
                    productNameInput.value = opt.dataset.name;
                    resultsDiv.style.display = 'none';
                    searchInput.value = '';
                });
            });
        } catch (e) {
            resultsDiv.innerHTML = `<div style="text-align:center;padding:10px;color:#f44336">Fehler: ${e.message}</div>`;
        }
    }
    
    searchBtn.addEventListener('click', searchProducts);
    searchInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            searchProducts();
        }
    });
    
    m.querySelector('#pu-save').addEventListener('click', async () => {
        const productId = Number.parseInt(productIdInput.value, 10);
        const url = document.getElementById('pu-url').value.trim();
        const selector = document.getElementById('pu-selector').value.trim();
        const updateInterval = document.getElementById('pu-interval').value;
        
        if (!productId || !url) {
            showToast('❌ Produkt und URL sind erforderlich', 'error');
            return;
        }
        
        try {
            const resp = await PluginAPI.fetch(pluginId, '/urls', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ product_id: productId, url, selector, update_interval: updateInterval }),
            });
            if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
            
            m.remove();
            loadUrls();
            showToast('✅ URL hinzugefügt');
        } catch (e) {
            showToast('❌ Fehler: ' + e.message, 'error');
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


function showToast(msg, type = 'info') {
    const existingToast = document.getElementById('plugin-toast');
    if (existingToast) existingToast.remove();
    
    const toast = document.createElement('div');
    toast.id = 'plugin-toast';
    toast.style.cssText = `
        position: fixed;
        bottom: 20px;
        right: 20px;
        padding: 12px 20px;
        border-radius: 8px;
        color: white;
        font-weight: 500;
        z-index: 10000;
        animation: slideIn 0.3s ease;
        max-width: 300px;
    `;
    
    const colors = {
        success: '#4caf50',
        error: '#f44336',
        info: '#2196f3'
    };
    toast.style.background = colors[type] || colors.info;
    toast.textContent = msg;
    
    const style = document.createElement('style');
    style.textContent = `
        @keyframes slideIn {
            from { transform: translateX(100%); opacity: 0; }
            to { transform: translateX(0); opacity: 1; }
        }
    `;
    document.head.appendChild(style);
    document.body.appendChild(toast);
    
    setTimeout(() => {
        toast.style.animation = 'slideIn 0.3s ease reverse';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}
