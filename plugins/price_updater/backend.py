from flask import Blueprint
import requests
from bs4 import BeautifulSoup
import logging

plugin_blueprint = Blueprint('price_updater', __name__)

logger = logging.getLogger('price_updater')


def _init_tables():
    """Erstellt die Plugin-spezifische Tabelle für URL-Mappings."""
    conn = get_db_connection()
    try:
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS price_updater_urls (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tenant_id TEXT NOT NULL,
            product_id INTEGER NOT NULL,
            url TEXT NOT NULL,
            selector TEXT,
            created INTEGER DEFAULT (strftime('%s','now')),
            updated INTEGER DEFAULT (strftime('%s','now')),
            UNIQUE(tenant_id, product_id)
        )''')
        conn.commit()
    finally:
        conn.close()


try:
    _init_tables()
except Exception as e:
    print(f'[price_updater] DB-Init Fehler: {e}')


def _extract_price_from_url(url, selector=None):
    """
    Extrahiert den Preis aus einer URL mittels Web Scraping.
    Unterstützt verschiedene Selektoren für verschiedene Händler.
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Wenn ein Selektor angegeben ist, diesen verwenden
        if selector:
            element = soup.select_one(selector)
            if element:
                price_text = element.get_text(strip=True)
                return _parse_price(price_text)
        
        # Amazon-Selektor
        amazon_price = soup.select_one('.a-price .a-offscreen')
        if amazon_price:
            return _parse_price(amazon_price.get_text(strip=True))
        
        # Allgemeine Preis-Selektoren
        price_selectors = [
            '.price',
            '.product-price',
            '[itemprop="price"]',
            '.price-value',
            '.current-price',
            '#priceblock_ourprice',
            '#priceblock_dealprice'
        ]
        
        for selector in price_selectors:
            element = soup.select_one(selector)
            if element:
                price = _parse_price(element.get_text(strip=True))
                if price > 0:
                    return price
        
        logger.warning(f'[price_updater] Kein Preis gefunden für URL: {url}')
        return None
        
    except Exception as e:
        logger.error(f'[price_updater] Fehler beim Abrufen von {url}: {e}')
        return None


def _parse_price(text):
    """Parst einen Preis-String und gibt den numerischen Wert zurück."""
    import re
    # Entferne alle Zeichen außer Zahlen, Komma und Punkt
    cleaned = re.sub(r'[^\d.,]', '', text)
    # Ersetze Komma durch Punkt für Dezimalzahlen
    cleaned = cleaned.replace(',', '.')
    try:
        return float(cleaned)
    except ValueError:
        return None


@plugin_blueprint.route('/urls', methods=['GET'])
@require_auth()
def get_urls():
    """Gibt alle konfigurierten URLs für den aktuellen Tenant zurück."""
    tenant_id = session.get('tenant_id')
    if not tenant_id:
        return json_response({'error': 'Kein Tenant'}, 401)
    
    conn = get_db_connection()
    try:
        c = conn.cursor()
        c.execute('''
            SELECT pu.id, pu.product_id, pu.url, pu.selector, p.name, p.ek
            FROM price_updater_urls pu
            JOIN products p ON pu.product_id = p.id
            WHERE pu.tenant_id = ?
            ORDER BY p.name
        ''', (tenant_id,))
        rows = c.fetchall()
        return json_response({'urls': [dict(r) for r in rows]})
    except Exception as e:
        logger.error(f'[price_updater] Fehler beim Abrufen der URLs: {e}')
        return json_response({'error': 'Interner Fehler'}, 500)
    finally:
        conn.close()


@plugin_blueprint.route('/urls', methods=['POST'])
@require_auth()
def add_url():
    """Fügt eine neue URL für ein Produkt hinzu."""
    tenant_id = session.get('tenant_id')
    if not tenant_id:
        return json_response({'error': 'Kein Tenant'}, 401)
    
    data = request.get_json(silent=True) or {}
    product_id = data.get('product_id')
    url = data.get('url', '').strip()
    selector = data.get('selector', '').strip()
    
    if not product_id or not url:
        return json_response({'error': 'product_id und url sind erforderlich'}, 400)
    
    conn = get_db_connection()
    try:
        c = conn.cursor()
        # Prüfen ob Produkt existiert
        c.execute('SELECT id FROM products WHERE id = ?', (product_id,))
        if not c.fetchone():
            return json_response({'error': 'Produkt nicht gefunden'}, 404)
        
        # URL hinzufügen oder aktualisieren
        c.execute('''
            INSERT OR REPLACE INTO price_updater_urls (tenant_id, product_id, url, selector, updated)
            VALUES (?, ?, ?, ?, strftime('%s','now'))
        ''', (tenant_id, product_id, url, selector))
        conn.commit()
        
        return json_response({'status': 'ok'})
    except Exception as e:
        logger.error(f'[price_updater] Fehler beim Hinzufügen der URL: {e}')
        return json_response({'error': 'Interner Fehler'}, 500)
    finally:
        conn.close()


@plugin_blueprint.route('/urls/<int:url_id>', methods=['DELETE'])
@require_auth()
def delete_url(url_id):
    """Löscht eine URL."""
    tenant_id = session.get('tenant_id')
    if not tenant_id:
        return json_response({'error': 'Kein Tenant'}, 401)
    
    conn = get_db_connection()
    try:
        c = conn.cursor()
        c.execute('DELETE FROM price_updater_urls WHERE id = ? AND tenant_id = ?', (url_id, tenant_id))
        conn.commit()
        
        if c.rowcount == 0:
            return json_response({'error': 'Nicht gefunden'}, 404)
        
        return json_response({'status': 'ok'})
    except Exception as e:
        logger.error(f'[price_updater] Fehler beim Löschen der URL: {e}')
        return json_response({'error': 'Interner Fehler'}, 500)
    finally:
        conn.close()


@plugin_blueprint.route('/update/<int:product_id>', methods=['POST'])
@require_auth()
def update_product_price(product_id):
    """Aktualisiert den EK-Preis eines einzelnen Produkts."""
    tenant_id = session.get('tenant_id')
    if not tenant_id:
        return json_response({'error': 'Kein Tenant'}, 401)
    
    conn = get_db_connection()
    try:
        c = conn.cursor()
        # URL für das Produkt abrufen
        c.execute('SELECT url, selector FROM price_updater_urls WHERE tenant_id = ? AND product_id = ?', (tenant_id, product_id))
        row = c.fetchone()
        
        if not row:
            return json_response({'error':('Keine URL für dieses Produkt konfiguriert')}, 404)
        
        url = row['url']
        selector = row['selector']
        
        # Preis abrufen
        new_price = _extract_price_from_url(url, selector if selector else None)
        
        if new_price is None:
            return json_response({'error': 'Preis konnte nicht extrahiert werden'}, 400)
        
        # Preis in der Datenbank aktualisieren
        c.execute('UPDATE products SET ek = ? WHERE id = ?', (new_price, product_id))
        conn.commit()
        
        logger.info(f'[price_updater] Preis für Produkt {product_id} aktualisiert: {new_price}€')
        
        return json_response({'status': 'ok', 'new_price': new_price})
    except Exception as e:
        logger.error(f'[price_updater] Fehler beim Aktualisieren des Preises: {e}')
        return json_response({'error': 'Interner Fehler'}, 500)
    finally:
        conn.close()


@plugin_blueprint.route('/update-all', methods=['POST'])
@require_auth()
def update_all_prices():
    """Aktualisiert alle konfigurierten Preise."""
    tenant_id = session.get('tenant_id')
    if not tenant_id:
        return json_response({'error': 'Kein Tenant'}, 401)
    
    conn = get_db_connection()
    try:
        c = conn.cursor()
        # Alle URLs für den Tenant abrufen
        c.execute('SELECT product_id, url, selector FROM price_updater_urls WHERE tenant_id = ?', (tenant_id,))
        rows = c.fetchall()
        
        results = []
        success_count = 0
        error_count = 0
        
        for row in rows:
            product_id = row['product_id']
            url = row['url']
            selector = row['selector']
            
            new_price = _extract_price_from_url(url, selector if selector else None)
            
            if new_price is not None:
                c.execute('UPDATE products SET ek = ? WHERE id = ?', (new_price, product_id))
                results.append({'product_id': product_id, 'status': 'ok', 'new_price': new_price})
                success_count += 1
            else:
                results.append({'product_id': product_id, 'status': 'error', 'message': 'Preis konnte nicht extrahiert werden'})
                error_count += 1
        
        conn.commit()
        
        logger.info(f'[price_updater] Massenaktualisierung: {success_count} erfolgreich, {error_count} fehlerhaft')
        
        return json_response({
            'status': 'ok',
            'results': results,
            'summary': {'success': success_count, 'error': error_count}
        })
    except Exception as e:
        logger.error(f'[price_updater] Fehler bei Massenaktualisierung: {e}')
        return json_response({'error': 'Interner Fehler'}, 500)
    finally:
        conn.close()
