from odoo import models, fields

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    google_api_key = fields.Char(string="Google API Key", config_parameter="product_search.google_api_key")
    google_cx = fields.Char(string="Google Search CX", config_parameter="product_search.google_cx")
