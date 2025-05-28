from odoo import api, fields, models, _
import requests
import re
from PIL import Image
import base64
from io import BytesIO

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    image_ids = fields.One2many('product.image', 'product_tmpl_id', string='Images')
    script = fields.Html('Script')

    def _es_imagen_valida(self, image_bytes):
        try:
            img = Image.open(BytesIO(image_bytes))
            width, height = img.size
            if width < 60 or height < 60:  # antes era 100x100
                return False
            colors = img.getcolors(maxcolors=256)
            if not colors or len(colors) <= 2:
                return False
            return True
        except Exception:
            return False

    def search_google_images(self):
        for product in self.filtered(lambda p: p.barcode):
            barcode = product.barcode
            api_key = 'AIzaSyAz1mcdCw-x9FQy_GJK0mkGUSqHh438bkE'
            cx = '3514c820cfa4f46ab'
            url = f'https://www.googleapis.com/customsearch/v1?q={barcode}&cx={cx}&searchType=image&key={api_key}'

            try:
                response = requests.get(url, timeout=30)
                response.raise_for_status()
            except requests.exceptions.RequestException:
                continue

            image_results = response.json().get('items', [])[:5]
            for image_result in image_results:
                try:
                    image_data = requests.get(image_result['link'], timeout=10).content
                    image_base64 = base64.b64encode(image_data).decode('utf-8')
                    self.env['product.image'].create({
                        'name': image_result['title'],
                        'image': image_base64,
                        'product_tmpl_id': product.id,
                    })
                except:
                    continue
        return True

    def search_google_images_by_name(self):
        for product in self.filtered(lambda p: p.name):
            product_name = product.name
            api_key = 'AIzaSyAz1mcdCw-x9FQy_GJK0mkGUSqHh438bkE'
            cx = '3514c820cfa4f46ab'
            url = f'https://www.googleapis.com/customsearch/v1?q={product_name}&cx={cx}&searchType=image&key={api_key}'

            try:
                response = requests.get(url, timeout=30)
                response.raise_for_status()
            except requests.exceptions.RequestException:
                continue

            image_results = response.json().get('items', [])[:5]
            for image_result in image_results:
                try:
                    image_data = requests.get(image_result['link'], timeout=10).content
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
        def extract_price_from_snippet(snippet):
            prices = re.findall(r'\$\s?\d+\.?\d*', snippet)
            if prices:
                prices = [float(price.replace('$', '').replace(' ', '')) for price in prices]
                return sum(prices) / len(prices)
            return 0

        for product in self:
            product_name = product.name
            api_key = 'AIzaSyAz1mcdCw-x9FQy_GJK0mkGUSqHh438bkE'
            cx = '3514c820cfa4f46ab'
            url = f'https://www.googleapis.com/customsearch/v1?q={product_name}&cx={cx}&key={api_key}&gl=cl&hl=es'

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
