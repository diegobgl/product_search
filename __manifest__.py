# -*- coding: utf-8 -*-
{
    'name': 'product_search',
    'summary': 'Busqueda de imagenes de producto en Google',
    'description': 'Busca imagenes en Google Custom Search y permite seleccionar una para el producto.',
    'author': 'DG software spa',
    'website': 'http://www.dgdev.cl',
    'category': 'Sales',
    'version': '0.1',
    'depends': ['base', 'product', 'sale'],
    'data': [
        'security/ir.model.access.csv',
        'views/product_template_view.xml',
        'views/google_image_wizard_views.xml',
        'views/product_boton_view.xml',
        'views/product_mass_actions.xml',
        'views/res_config_settings_views.xml',
    ],
    'demo': [
        'demo/demo.xml',
    ],
}
