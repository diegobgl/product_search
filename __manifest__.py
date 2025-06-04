# -*- coding: utf-8 -*-
{
    'name': "product_search",

    'summary': """
        aplicacion para buscar imagenes de un producto por codigo de barras en google""",

    'description': """
        Buscador de imagenes por producto
    """,

    'author': "DG software spa",
    'website': "http://www.dgdev.cl",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/12.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','sale'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/product_template_view.xml',
        'views/google_image_wizard_views.xml',
        'views/product_boton_view.xml',
        'views/product_mass_actions.xml',
        'views/res_config_settings_views.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}