# -*- coding: utf-8 -*-
from odoo import http

# class ProductSearch(http.Controller):
#     @http.route('/product_search/product_search/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/product_search/product_search/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('product_search.listing', {
#             'root': '/product_search/product_search',
#             'objects': http.request.env['product_search.product_search'].search([]),
#         })

#     @http.route('/product_search/product_search/objects/<model("product_search.product_search"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('product_search.object', {
#             'object': obj
#         })