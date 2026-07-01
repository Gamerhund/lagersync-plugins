/* ═══════════════════════════════════════════════════════════════
   Profi Design Plugin – frontend.js
   Fügt unter den Menüpunkt 🎨 Design → Web Design hinzu.
   Nutzer können zwischen Standard-Design und Profi-Design wählen.
   ═══════════════════════════════════════════════════════════════ */

(function () {
  const pluginId = 'pro-design';
  const STORAGE_KEY = 'lagersync_web_design';
  const STYLE_ID    = 'profi-design-overrides';

  /* ── CSS-Overrides für das Profi-Design ───────────────────────── */
  const PROFI_CSS = `
    /* === Profi Design: Klarer, minimaler Stil === */

    body.profi-design,
    html.profi-design {
      font-family: Inter, system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
    }

    body.profi-design {
      background: linear-gradient(160deg, #0d1b2a 0%, #0f2338 50%, #122840 100%) !important;
      color: #e6f0fb !important;
    }
    html.profi-design {
      background: linear-gradient(160deg, #0d1b2a 0%, #0f2338 50%, #122840 100%) !important;
    }

    /* ── Locations-Grid ── */
    body.profi-design .location-card {
      background: linear-gradient(180deg, rgba(255,255,255,0.045) 0%, rgba(255,255,255,0.015) 100%) !important;
      border: 1.5px solid rgba(255,255,255,0.09) !important;
      border-radius: 14px !important;
      box-shadow: 0 4px 18px rgba(0,0,0,0.25) !important;
      padding: 22px !important;
      transition: border-color 0.2s, transform 0.2s, box-shadow 0.2s !important;
    }
    body.profi-design .location-card:hover {
      transform: translateY(-4px) !important;
      border-color: rgba(255, 107, 53, 0.45) !important;
      box-shadow: 0 8px 28px rgba(0,0,0,0.35) !important;
    }
    body.profi-design .location-card h3 {
      font-weight: 600 !important;
      letter-spacing: -0.01em !important;
    }
    body.profi-design .location-card .count {
      font-size: 2.4em !important;
      font-weight: 700 !important;
      text-shadow: none !important;
      opacity: 0.95 !important;
    }

    /* ── Header ── */
    body.profi-design .header h1 {
      font-weight: 700 !important;
      letter-spacing: -0.03em !important;
    }

    /* ── Produkt-Items ── */
    body.profi-design .product-item {
      background: rgba(255,255,255,0.04) !important;
      border: 1px solid rgba(255,255,255,0.08) !important;
      border-radius: 10px !important;
      backdrop-filter: none !important;
    }
    body.profi-design .product-item:hover {
      background: rgba(255,255,255,0.07) !important;
      border-color: rgba(255,107,53,0.3) !important;
    }

    /* ── Inventory-Items ── */
    body.profi-design .inventory-item {
      background: rgba(255,255,255,0.04) !important;
      border: 1px solid rgba(255,255,255,0.07) !important;
      border-radius: 10px !important;
    }

    /* ── Buttons (allgemein) ── */
    body.profi-design .btn {
      background: rgba(255,255,255,0.08) !important;
      border: 1px solid rgba(255,255,255,0.12) !important;
      border-radius: 9px !important;
      box-shadow: none !important;
      font-weight: 500 !important;
      transition: background 0.15s, border-color 0.15s !important;
    }
    body.profi-design .btn:hover {
      background: rgba(255,255,255,0.13) !important;
      border-color: rgba(255,255,255,0.2) !important;
      filter: none !important;
    }
    /* Scan-Button orange beibehalten */
    body.profi-design .btn-scan {
      background: linear-gradient(135deg, #FF6B35 0%, #FF5722 100%) !important;
      border: none !important;
    }

    /* ── Modal ── */
    body.profi-design .modal-content {
      background: linear-gradient(160deg, #0f2237 0%, #0d1e30 100%) !important;
      border: 1px solid rgba(255,255,255,0.12) !important;
      border-radius: 16px !important;
      box-shadow: 0 20px 60px rgba(0,0,0,0.5) !important;
    }
    body.profi-design .modal-content input,
    body.profi-design .modal-content select,
    body.profi-design .modal-content textarea {
      background: rgba(255,255,255,0.06) !important;
      border: 1.5px solid rgba(255,255,255,0.12) !important;
      border-radius: 8px !important;
    }
    body.profi-design .modal-content input:focus,
    body.profi-design .modal-content select:focus,
    body.profi-design .modal-content textarea:focus {
      border-color: rgba(255,107,53,0.6) !important;
      outline: none !important;
      box-shadow: 0 0 0 3px rgba(255,107,53,0.1) !important;
    }

    /* ── Settings-Menü ── */
    body.profi-design .settings-menu {
      background: rgba(10, 25, 40, 0.97) !important;
      border: 1px solid rgba(255,255,255,0.1) !important;
      border-radius: 14px !important;
      box-shadow: 0 12px 40px rgba(0,0,0,0.4) !important;
    }
    body.profi-design .settings-menu button {
      background: rgba(255,255,255,0.05) !important;
      border: 1px solid rgba(255,255,255,0.08) !important;
      border-radius: 8px !important;
      font-weight: 500 !important;
    }
    body.profi-design .settings-menu button:hover {
      background: rgba(255,255,255,0.1) !important;
    }

    /* ── Qty-Buttons ── */
    body.profi-design .qty-btn {
      border-radius: 8px !important;
      font-weight: 700 !important;
    }

    /* ── Scrollbar ── */
    body.profi-design ::-webkit-scrollbar { width: 6px; }
    body.profi-design ::-webkit-scrollbar-track { background: transparent; }
    body.profi-design ::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.15); border-radius: 3px; }
    body.profi-design ::-webkit-scrollbar-thumb:hover { background: rgba(255,255,255,0.25); }
  `;

  /* ── Design anwenden / entfernen ─────────────────────────────── */
  function applyProfiDesign() {
    document.documentElement.classList.add('profi-design');
    document.body.classList.add('profi-design');
    let style = document.getElementById(STYLE_ID);
    if (!style) {
      style = document.createElement('style');
      style.id = STYLE_ID;
      document.head.appendChild(style);
    }
    style.textContent = PROFI_CSS;
  }

  function removeProfiDesign() {
    document.documentElement.classList.remove('profi-design');
    document.body.classList.remove('profi-design');
    const style = document.getElementById(STYLE_ID);
    if (style) style.remove();
  }

  function setDesign(mode) {
    localStorage.setItem(STORAGE_KEY, mode);
    if (mode === 'profi') {
      applyProfiDesign();
    } else {
      removeProfiDesign();
    }
    updateActiveState(mode);
  }

  function getCurrentDesign() {
    return localStorage.getItem(STORAGE_KEY) || 'standard';
  }

  /* ── Modal: Design-Auswahl ───────────────────────────────────── */
  function updateActiveState(mode) {
    const modal = document.getElementById('profi-design-modal');
    if (!modal) return;
    modal.querySelectorAll('.pdd-option').forEach(el => {
      el.classList.toggle('pdd-active', el.dataset.mode === mode);
    });
  }

  function openDesignModal() {
    const existingModal = document.getElementById('profi-design-modal');
    if (existingModal) {
      existingModal.style.display = 'flex';
      updateActiveState(getCurrentDesign());
      return;
    }

    const modal = document.createElement('div');
    modal.id = 'profi-design-modal';
    modal.style.cssText = `
      display: flex; position: fixed; inset: 0;
      background: rgba(0,0,0,0.65); z-index: 99999;
      align-items: center; justify-content: center;
      backdrop-filter: blur(6px); padding: 20px;
      font-family: Inter, 'Segoe UI', sans-serif;
    `;

    modal.innerHTML = `
      <div style="
        background: linear-gradient(160deg, #0f2237 0%, #0d1e30 100%);
        border: 1px solid rgba(255,255,255,0.13);
        border-radius: 20px;
        padding: 32px 28px;
        max-width: 480px;
        width: 100%;
        box-shadow: 0 24px 70px rgba(0,0,0,0.55);
        color: #e6f0fb;
        animation: pdd-slide 0.25s ease;
      ">
        <style>
          @keyframes pdd-slide {
            from { opacity: 0; transform: translateY(16px) scale(0.97); }
            to   { opacity: 1; transform: translateY(0)    scale(1); }
          }
          .pdd-option {
            display: flex; align-items: center; gap: 16px;
            padding: 18px 20px; border-radius: 14px;
            border: 2px solid rgba(255,255,255,0.08);
            background: rgba(255,255,255,0.04);
            cursor: pointer; transition: all 0.18s;
            margin-bottom: 12px; user-select: none;
          }
          .pdd-option:hover {
            background: rgba(255,255,255,0.08);
            border-color: rgba(255,255,255,0.18);
          }
          .pdd-option.pdd-active {
            border-color: #FF6B35;
            background: rgba(255,107,53,0.1);
            box-shadow: 0 0 0 1px rgba(255,107,53,0.25);
          }
          .pdd-option .pdd-preview {
            width: 56px; height: 40px; border-radius: 8px; flex-shrink: 0;
            overflow: hidden; border: 1px solid rgba(255,255,255,0.1);
          }
          .pdd-option .pdd-info h4 {
            font-weight: 600; font-size: 15px; margin: 0 0 4px 0;
          }
          .pdd-option .pdd-info p {
            font-size: 12px; color: rgba(230,240,251,0.6); margin: 0; line-height: 1.4;
          }
          .pdd-option .pdd-check {
            margin-left: auto; width: 22px; height: 22px; border-radius: 50%;
            background: rgba(255,255,255,0.08); display: flex; align-items: center;
            justify-content: center; font-size: 12px; flex-shrink: 0;
            border: 1.5px solid rgba(255,255,255,0.15);
          }
          .pdd-option.pdd-active .pdd-check {
            background: #FF6B35; border-color: #FF6B35; color: #fff;
          }
        </style>

        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:24px;">
          <div>
            <h2 style="font-size:20px;font-weight:700;margin:0 0 4px 0;letter-spacing:-0.02em;">🎨 Web Design</h2>
            <p style="font-size:13px;color:rgba(230,240,251,0.5);margin:0;">Wähle deinen bevorzugten Stil</p>
          </div>
          <button onclick="document.getElementById('profi-design-modal').style.display='none'"
            style="background:rgba(255,255,255,0.07);border:1px solid rgba(255,255,255,0.12);
                   color:#e6f0fb;width:36px;height:36px;border-radius:9px;cursor:pointer;
                   font-size:16px;display:flex;align-items:center;justify-content:center;">✕</button>
        </div>

        <!-- Option: Standard -->
        <div class="pdd-option" data-mode="standard" onclick="window._profiDesignPlugin.set('standard')">
          <div class="pdd-preview" style="background:linear-gradient(135deg,#1e3c72,#2a5298);">
            <div style="background:#FF6B35;height:8px;width:100%;"></div>
            <div style="padding:4px 5px;">
              <div style="background:rgba(255,255,255,0.2);height:5px;border-radius:2px;margin-bottom:3px;"></div>
              <div style="background:rgba(255,255,255,0.1);height:5px;border-radius:2px;width:70%;"></div>
            </div>
          </div>
          <div class="pdd-info">
            <h4>Standard</h4>
            <p>Klassisches Blau-Design mit bunten Karten und lebhaften Farben</p>
          </div>
          <div class="pdd-check">✓</div>
        </div>

        <!-- Option: Profi -->
        <div class="pdd-option" data-mode="profi" onclick="window._profiDesignPlugin.set('profi')">
          <div class="pdd-preview" style="background:linear-gradient(135deg,#0d1b2a,#0f2338);">
            <div style="background:rgba(255,255,255,0.05);height:8px;width:100%;border-bottom:1px solid rgba(255,255,255,0.07);"></div>
            <div style="padding:4px 5px;">
              <div style="background:rgba(255,255,255,0.06);height:5px;border-radius:2px;margin-bottom:3px;border:1px solid rgba(255,255,255,0.05);"></div>
              <div style="background:rgba(255,255,255,0.04);height:5px;border-radius:2px;width:70%;border:1px solid rgba(255,255,255,0.04);"></div>
            </div>
          </div>
          <div class="pdd-info">
            <h4>Profi Design</h4>
            <p>Klares, minimales Dunkelblau mit Inter-Schrift und feinen Rändern</p>
          </div>
          <div class="pdd-check">✓</div>
        </div>

        <p style="font-size:11px;color:rgba(230,240,251,0.3);text-align:center;margin-top:8px;">
          Einstellung wird automatisch gespeichert
        </p>
      </div>
    `;

    /* Klick außerhalb schließt Modal */
    modal.addEventListener('click', e => {
      if (e.target === modal) modal.style.display = 'none';
    });

    document.body.appendChild(modal);
    updateActiveState(getCurrentDesign());
  }

  /* ── Globale Referenz für onclick-Handler im Modal ───────────── */
  window._profiDesignPlugin = {
    set: setDesign,
    open: openDesignModal,
  };

  /* ── Beim Start: gespeichertes Design laden ──────────────────── */
  if (getCurrentDesign() === 'profi') {
    applyProfiDesign();
  }

  /* ── Menü-Eintrag im Design-Center hinzufügen ─────────────────── */
  function addWebDesignButtonToDesignCenter() {
    // Patch die openDesignCenter-Funktion, um den Web Design Button hinzuzufügen
    const originalOpenDesignCenter = window.openDesignCenter;
    if (originalOpenDesignCenter) {
      window.openDesignCenter = function() {
        originalOpenDesignCenter();
        // Warte kurz bis das Modal gerendert ist
        setTimeout(() => {
          const modal = document.getElementById('designCenterModal');
          if (modal) {
            const buttonContainer = modal.querySelector('.modal-content > div[style*="display:grid"]');
            if (buttonContainer) {
              // Prüfen ob der Button schon existiert
              if (!buttonContainer.querySelector('.profi-design-btn')) {
                const webDesignBtn = document.createElement('button');
                webDesignBtn.className = 'btn btn-overview profi-design-btn';
                webDesignBtn.innerHTML = '🌐 Web Design';
                webDesignBtn.onclick = function() {
                  document.getElementById('designCenterModal').remove();
                  openDesignModal();
                };
                buttonContainer.appendChild(webDesignBtn);
              }
            }
          }
        }, 50);
      };
    }
  }

  try {
    addWebDesignButtonToDesignCenter();
  } catch (e) {
    /* Fallback: warte bis die Seite geladen ist */
    window.addEventListener('load', () => {
      try { addWebDesignButtonToDesignCenter(); } catch (_) {}
    });
  }

})();
