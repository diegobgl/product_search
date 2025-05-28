from odoo import models, fields, api

class GoogleImageWizard(models.TransientModel):
    _name = 'googleimage.wizard'
    _description = 'Google Image Wizard'

    image_datas = fields.Binary(string='Imágenes de Google')

 
    def save_images_to_product(self):
        active_product = self.env['product.template'].browse(self.env.context.get('active_id'))
        active_product.write({'image_medium': self.image_datas})

