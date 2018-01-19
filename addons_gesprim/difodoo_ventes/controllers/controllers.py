# -*- coding: utf-8 -*-
from odoo import http

# class Gesprim(http.Controller):
#     @http.route('/gesprim/gesprim/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/gesprim/gesprim/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('gesprim.listing', {
#             'root': '/gesprim/gesprim',
#             'objects': http.request.env['gesprim.gesprim'].search([]),
#         })

#     @http.route('/gesprim/gesprim/objects/<model("gesprim.gesprim"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('gesprim.object', {
#             'object': obj
#         })