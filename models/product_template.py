from odoo import api, fields, models, _
import requests
import re
from PIL import Image
import base64
from io import BytesIO
from odoo.exceptions import UserError


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    image_ids = fields.One2many('product.image', 'product_tmpl_id', string='Images')
    script = fields.Html('Script')

    def _get_google_config(self):
        api_key = self.env['ir.config_parameter'].sudo().get_param('product_search.google_api_key')
        cx = self.env['ir.config_parameter'].sudo().get_param('product_search.google_cx')
        return api_key, cx

    def _es_imagen_valida(self, image_data):
        try:
            image_process.image_data_from_base64(base64.b64encode(image_data))
            return True
        except Exception:
            return False

    def search_google_images(self):
        api_key, cx = self._get_google_config()
        for product in self.filtered(lambda p: p.barcode):
            if not api_key or not cx:
                continue

            search_url = 'https://www.googleapis.com/customsearch/v1'
            params = {
                'q': product.barcode,
                'cx': cx,
                'key': api_key,
                'searchType': 'image',
                'gl': 'cl',
                'imgType': 'photo',
                'num': 10,
            }

            try:
                response = requests.get(search_url, params=params, timeout=30)
                response.raise_for_status()
                image_results = response.json().get('items', [])
            except requests.exceptions.RequestException as e:
                _logger.warning(f"Google API request failed for product {product.barcode}: {e}")
                continue

            used_urls = set()
            for image_result in image_results:
                image_url = image_result.get('link', '')
                title = image_result.get('title', 'Imagen')
                mime_type = image_result.get('mime', '')

                if not image_url or image_url in used_urls:
                    continue

                if not mime_type.startswith('image/') or not image_url.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
                    continue

                try:
                    image_response = requests.get(image_url, timeout=10)
                    image_response.raise_for_status()
                    image_data = image_response.content

                    if not self._es_imagen_valida(image_data):
                        continue

                    image_base64 = base64.b64encode(image_data).decode('utf-8')
                    self.env['product.image'].create({
                        'name': title,
                        'image': image_base64,
                        'product_tmpl_id': product.id,
                    })
                    used_urls.add(image_url)

                except Exception as e:
                    _logger.debug(f"Failed to process image: {e}")
                    continue

        return True

    def search_google_images_by_name(self):
        api_key, cx = self._get_google_config()
        for product in self.filtered(lambda p: p.name):
            if not api_key or not cx:
                continue
            url = f'https://www.googleapis.com/customsearch/v1?q={product.name}&cx={cx}&searchType=image&key={api_key}&gl=cl'

            try:
                response = requests.get(url, timeout=30)
                response.raise_for_status()
            except requests.exceptions.RequestException:
                continue

            image_results = response.json().get('items', [])[:5]
            for image_result in image_results:
                try:
                    image_data = requests.get(image_result['link'], timeout=10).content
                    if self._es_imagen_valida(image_data):
                        image_base64 = base64.b64encode(image_data).decode('utf-8')
                        self.env['product.image'].create({
                            'name': image_result['title'],
                            'image': image_base64,
                            'product_tmpl_id': product.id,
                        })
                except:
                    continue
        return True

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
        api_key, cx = self._get_google_config()

        def extract_price_from_snippet(snippet):
            prices = re.findall(r'\$\s?\d+\.?\d*', snippet)
            if prices:
                prices = [float(price.replace('$', '').replace(' ', '')) for price in prices]
                return sum(prices) / len(prices)
            return 0

        for product in self:
            if not api_key or not cx:
                continue
            url = f'https://www.googleapis.com/customsearch/v1?q={product.name}&cx={cx}&key={api_key}&gl=cl&hl=es'

            try:
                response = requests.get(url, timeout=30)
                response.raise_for_status()
            except requests.exceptions.RequestException:
                continue

            response_json = response.json()
            text_results = response_json.get('items', [])[:3]
            brief_text = min(text_results, key=lambda x: len(x.get('snippet', '')))['snippet'] if text_results else ''
            prices = [extract_price_from_snippet(result.get('snippet', '')) for result in text_results]
            prices = [price for price in prices if price > 0]
            average_price = sum(prices) / len(prices) if prices else 0

            product.description = f'Descripción: {brief_text}\nPrecio promedio: ${average_price:.2f}'
        return True


class ProductImage(models.Model):
    _name = 'product.image'

    name = fields.Char(string='Name')
    image = fields.Binary(string='Image')
    product_tmpl_id = fields.Many2one('product.template', string='Product')
