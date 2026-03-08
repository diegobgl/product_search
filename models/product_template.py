import base64
import logging
import re
from io import BytesIO

import requests
from PIL import Image

from odoo import _, fields, models
from odoo.exceptions import UserError


_LOGGER = logging.getLogger(__name__)


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    image_ids = fields.One2many('product.image', 'product_tmpl_id', string='Images')
    script = fields.Html('Script')

    def _get_google_config(self):
        api_key = self.env['ir.config_parameter'].sudo().get_param('product_search.google_api_key')
        cx = self.env['ir.config_parameter'].sudo().get_param('product_search.google_cx')
        return api_key, cx

    def _get_google_search_params(self, query, search_type=None):
        api_key, cx = self._get_google_config()
        if not api_key or not cx:
            raise UserError(_('Configure Google API Key y Search Engine ID (CX) en Ajustes antes de buscar imagenes.'))

        params = {
            'q': query,
            'cx': cx,
            'key': api_key,
            'gl': 'cl',
            'hl': 'es',
            'num': 5,
        }
        if search_type:
            params['searchType'] = search_type
        return params

    def _es_imagen_valida(self, image_data):
        try:
            image = Image.open(BytesIO(image_data))
            image.verify()
            return True
        except Exception:
            return False

    def _download_image_as_base64(self, image_url):
        if not image_url:
            return False
        try:
            response = requests.get(image_url, timeout=15)
            response.raise_for_status()
        except requests.exceptions.RequestException as exc:
            _LOGGER.warning('No se pudo descargar la imagen %s: %s', image_url, exc)
            return False

        if not self._es_imagen_valida(response.content):
            return False
        return base64.b64encode(response.content).decode('utf-8')

    def _fetch_google_image_results(self, query):
        try:
            response = requests.get(
                'https://www.googleapis.com/customsearch/v1',
                params=self._get_google_search_params(query, search_type='image'),
                timeout=30,
            )
            response.raise_for_status()
        except requests.exceptions.RequestException as exc:
            raise UserError(_('Google no respondio correctamente: %s') % exc) from exc

        results = []
        for item in response.json().get('items', []):
            image_base64 = self._download_image_as_base64(item.get('link'))
            if not image_base64:
                continue
            results.append({
                'name': item.get('title') or _('Imagen de Google'),
                'image_url': item.get('link'),
                'source_url': item.get('image', {}).get('contextLink') or item.get('displayLink'),
                'image_1920': image_base64,
            })
        return results

    def _open_google_image_wizard(self, query):
        self.ensure_one()
        results = self._fetch_google_image_results(query)
        if not results:
            raise UserError(_('No se encontraron imagenes validas para "%s".') % query)

        wizard = self.env['googleimage.wizard'].create({
            'product_tmpl_id': self.id,
            'search_query': query,
            'result_line_ids': [(0, 0, values) for values in results],
        })
        if wizard.result_line_ids:
            wizard.selected_line_id = wizard.result_line_ids[0].id
        return wizard._get_action()

    def search_google_images(self):
        self.ensure_one()
        if not self.barcode:
            raise UserError(_('El producto no tiene codigo de barras.'))
        return self._open_google_image_wizard(self.barcode)

    def search_google_images_by_name(self):
        self.ensure_one()
        if not self.name:
            raise UserError(_('El producto no tiene nombre.'))
        return self._open_google_image_wizard(self.name)

    def set_main_image(self):
        self.ensure_one()
        image = self.image_ids[:1]
        if image:
            self.image_1920 = image.image
        return True

    def delete_all_images(self):
        self.ensure_one()
        self.image_ids.unlink()
        return True

    def search_google_info(self):
        def extract_price_from_snippet(snippet):
            prices = re.findall(r'\$\s?\d+\.?\d*', snippet)
            if prices:
                values = [float(price.replace('$', '').replace(' ', '')) for price in prices]
                return sum(values) / len(values)
            return 0

        for product in self:
            try:
                response = requests.get(
                    'https://www.googleapis.com/customsearch/v1',
                    params=product._get_google_search_params(product.name),
                    timeout=30,
                )
                response.raise_for_status()
            except requests.exceptions.RequestException as exc:
                raise UserError(_('No fue posible obtener informacion desde Google: %s') % exc) from exc

            response_json = response.json()
            text_results = response_json.get('items', [])[:3]
            brief_text = min(text_results, key=lambda x: len(x.get('snippet', '')))['snippet'] if text_results else ''
            prices = [extract_price_from_snippet(result.get('snippet', '')) for result in text_results]
            prices = [price for price in prices if price > 0]
            average_price = sum(prices) / len(prices) if prices else 0
            product.description_sale = 'Descripcion: %s\nPrecio promedio: $%.2f' % (brief_text, average_price)
        return True


class ProductImage(models.Model):
    _name = 'product.image'
    _description = 'Selected external product image'

    name = fields.Char(string='Name')
    image = fields.Binary(string='Image')
    source_url = fields.Char(string='Source URL')
    product_tmpl_id = fields.Many2one('product.template', string='Product')
