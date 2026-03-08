from odoo import _, api, fields, models
from odoo.exceptions import UserError


class GoogleImageWizard(models.TransientModel):
    _name = 'googleimage.wizard'
    _description = 'Google Image Wizard'

    product_tmpl_id = fields.Many2one('product.template', string='Product', required=True)
    search_query = fields.Char(string='Search query', readonly=True)
    result_line_ids = fields.One2many('googleimage.wizard.line', 'wizard_id', string='Results')
    selected_line_id = fields.Many2one('googleimage.wizard.line', string='Selected image')
    selected_image = fields.Binary(related='selected_line_id.image_1920', string='Selected preview', readonly=True)
    selected_source_url = fields.Char(related='selected_line_id.source_url', string='Source', readonly=True)

    def _get_action(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Seleccionar imagen'),
            'res_model': 'googleimage.wizard',
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'new',
        }

    def action_save_selected_image(self):
        self.ensure_one()
        if not self.selected_line_id:
            raise UserError(_('Seleccione una imagen antes de guardar.'))

        selected = self.selected_line_id
        image_model = self.env['product.image']
        existing_image = image_model.search([
            ('product_tmpl_id', '=', self.product_tmpl_id.id),
            ('source_url', '=', selected.source_url),
        ], limit=1)

        values = {
            'name': selected.name,
            'image': selected.image_1920,
            'source_url': selected.source_url,
            'product_tmpl_id': self.product_tmpl_id.id,
        }
        if existing_image:
            existing_image.write(values)
        else:
            image_model.create(values)

        self.product_tmpl_id.image_1920 = selected.image_1920
        return {'type': 'ir.actions.act_window_close'}


class GoogleImageWizardLine(models.TransientModel):
    _name = 'googleimage.wizard.line'
    _description = 'Google Image Wizard Line'
    _order = 'id'

    wizard_id = fields.Many2one('googleimage.wizard', required=True, ondelete='cascade')
    name = fields.Char(string='Title', readonly=True)
    image_1920 = fields.Binary(string='Image', readonly=True)
    image_url = fields.Char(string='Image URL', readonly=True)
    source_url = fields.Char(string='Source URL', readonly=True)
    is_selected = fields.Boolean(string='Selected', compute='_compute_is_selected')

    @api.depends('wizard_id.selected_line_id')
    def _compute_is_selected(self):
        for line in self:
            line.is_selected = line.wizard_id.selected_line_id == line

    def action_select(self):
        self.ensure_one()
        self.wizard_id.selected_line_id = self.id
        return self.wizard_id._get_action()
