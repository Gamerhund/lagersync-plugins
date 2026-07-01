from flask import Blueprint
import requests
from bs4 import BeautifulSoup
import logging
import json

plugin_blueprint = Blueprint('price_updater', __name__)

logger = logging.getLogger('price_updater')

ERROR_NO_TENANT = 'Kein Tenant'
ERROR_INTERNAL = 'Interner Fehler'


def _init_tables():
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


def _extract_price_from_json_ld(soup):
    for script in soup.find_all('script', type='application/ld+json'):
        if not script.string:
            continue
        try:
            data = json.loads(script.string)
        except json.JSONDecodeError:
            continue
        
        json_str = json.dumps(data)
        if 'price' not in json_str.lower():
            continue
        
        obj = data
        if isinstance(data, dict) and 'object' in data:
            obj = data['object']
        
        if not isinstance(obj, dict) or 'offers' not in obj:
            continue
        
        offers = obj['offers']
        if isinstance(offers, dict) and 'price' in offers:
            try:
                return float(offers['price'])
            except (ValueError, TypeError):
                continue
        
        if isinstance(offers, list) and len(offers) > 0:
            first_offer = offers[0]
            if isinstance(first_offer, dict) and 'price' in first_offer:
                try:
                    return float(first_offer['price'])
                except (ValueError, TypeError):
                    continue
    
    return None


def _extract_price_from_selectors(soup, selectors):
    for selector in selectors:
        element = soup.select_one(selector)
        if element:
            price = _parse_price(element.get_text(strip=True))
            if price and price > 0:
                return price
    return None


def _extract_price_from_url(url, selector=None):
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        if selector:
            element = soup.select_one(selector)
            if element:
                price_text = element.get_text(strip=True)
                return _parse_price(price_text)
        
        amazon_price = soup.select_one('.a-price .a-offscreen')
        if amazon_price:
            return _parse_price(amazon_price.get_text(strip=True))
        
        price_selectors = [
            '.price',
            '.product-price',
            '[itemprop="price"]',
            '.price-value',
            '.current-price',
            '#priceblock_ourprice',
            '#priceblock_dealprice'
        ]
        
        price = _extract_price_from_selectors(soup, price_selectors)
        if price:
            return price
        
        price = _extract_price_from_json_ld(soup)
        if price:
            return price
        
        logger.warning(f'[price_updater] Kein Preis gefunden für URL: {url}')
        return None
        
    except Exception:
        logger.exception(f'[price_updater] Fehler beim Abrufen von {url}')
        return None


def _parse_price(text):
    import re
    cleaned = re.sub(r'[^\d.,]', '', text)
    cleaned = cleaned.replace(',', '.')
    try:
        return float(cleaned)
    except ValueError:
        return None


@plugin_blueprint.route('/urls', methods=['GET'])
@require_auth()
def get_urls():
    tenant_id = session.get('tenant_id')
    if not tenant_id:
        return json_response({'error': ERROR_NO_TENANT}, 401)
    
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
    except Exception:
        logger.exception('[price_updater] Fehler beim Abrufen der URLs')
        return json_response({'error': ERROR_INTERNAL}, 500)
    finally:
        conn.close()


@plugin_blueprint.route('/urls', methods=['POST'])
@require_auth()
def add_url():
    tenant_id = session.get('tenant_id')
    if not tenant_id:
        return json_response({'error': ERROR_NO_TENANT}, 401)
    
    data = request.get_json(silent=True) or {}
    product_id = data.get('product_id')
    url = data.get('url', '').strip()
    selector = data.get('selector', '').strip()
    
    if not product_id or not url:
        return json_response({'error': 'product_id und url sind erforderlich'}, 400)
    
    conn = get_db_connection()
    try:
        c = conn.cursor()
        c.execute('SELECT id FROM products WHERE id = ?', (product_id,))
        if not c.fetchone():
            return json_response({'error': 'Produkt nicht gefunden'}, 404)
        
        c.execute('''
            INSERT OR REPLACE INTO price_updater_urls (tenant_id, product_id, url, selector, updated)
            VALUES (?, ?, ?, ?, strftime('%s','now'))
        ''', (tenant_id, product_id, url, selector))
        conn.commit()
        
        return json_response({'status': 'ok'})
    except Exception:
        logger.exception('[price_updater] Fehler beim Hinzufügen der URL')
        return json_response({'error': ERROR_INTERNAL}, 500)
    finally:
        conn.close()


@plugin_blueprint.route('/urls/<int:url_id>', methods=['DELETE'])
@require_auth()
def delete_url(url_id):
    tenant_id = session.get('tenant_id')
    if not tenant_id:
        return json_response({'error': ERROR_NO_TENANT}, 401)
    
    conn = get_db_connection()
    try:
        c = conn.cursor()
        c.execute('DELETE FROM price_updater_urls WHERE id = ? AND tenant_id = ?', (url_id, tenant_id))
        conn.commit()
        
        if c.rowcount == 0:
            return json_response({'error': 'Nicht gefunden'}, 404)
        
        return json_response({'status': 'ok'})
    except Exception:
        logger.exception('[price_updater] Fehler beim Löschen der URL')
        return json_response({'error': ERROR_INTERNAL}, 500)
    finally:
        conn.close()


@plugin_blueprint.route('/update/<int:product_id>', methods=['POST'])
@require_auth()
def update_product_price(product_id):
    tenant_id = session.get('tenant_id')
    if not tenant_id:
        return json_response({'error': ERROR_NO_TENANT}, 401)
    
    conn = get_db_connection()
    try:
        c = conn.cursor()
        c.execute('SELECT url, selector FROM price_updater_urls WHERE tenant_id = ? AND product_id = ?', (tenant_id, product_id))
        row = c.fetchone()
        
        if not row:
            return json_response({'error':('Keine URL für dieses Produkt konfiguriert')}, 404)
        
        url = row['url']
        selector = row['selector']
        
        new_price = _extract_price_from_url(url, selector if selector else None)
        
        if new_price is None:
            return json_response({'error': 'Preis konnte nicht extrahiert werden'}, 400)
        
        c.execute('UPDATE products SET ek = ? WHERE id = ? AND id IN (SELECT product_id FROM price_updater_urls WHERE tenant_id = ?)', (new_price, product_id, tenant_id))
        conn.commit()
        
        logger.info(f'[price_updater] Preis für Produkt {product_id} aktualisiert: {new_price}€')
        
        return json_response({'status': 'ok', 'new_price': new_price})
    except Exception:
        logger.exception('[price_updater] Fehler beim Aktualisieren des Preises')
        return json_response({'error': ERROR_INTERNAL}, 500)
    finally:
        conn.close()


@plugin_blueprint.route('/update-all', methods=['POST'])
@require_auth()
def update_all_prices():
    tenant_id = session.get('tenant_id')
    if not tenant_id:
        return json_response({'error': ERROR_NO_TENANT}, 401)
    
    conn = get_db_connection()
    try:
        c = conn.cursor()
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
                c.execute('UPDATE products SET ek = ? WHERE id = ? AND id IN (SELECT product_id FROM price_updater_urls WHERE tenant_id = ?)', (new_price, product_id, tenant_id))
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
    except Exception:
        logger.exception('[price_updater] Fehler bei Massenaktualisierung')
        return json_response({'error': ERROR_INTERNAL}, 500)
    finally:
        conn.close()
