# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import time

from odoo import api, fields, models, _
import datetime


class DiProductResserre(models.TransientModel):
    _name = 'di.product.resserre'
    _description = 'Resserre produit'
    
    di_to_date = fields.Date('Le', default=time.strftime('%Y-%m-%d') )
   
    @api.multi
    def action_open_window(self):
        self.ensure_one()
        context = dict(self.env.context or {})
        domain = []

        def ref(module, xml_id):
            proxy = self.env['ir.model.data']
            return proxy.get_object_reference(module, xml_id)
# 
        model, search_view_id = ref('product', 'product_search_form_view')
#         model, graph_view_id = ref('product_margin', 'view_product_margin_graph')
#         model, form_view_id = ref('product_margin', 'view_product_margin_form')
        model, tree_view_id = ref('difodoo_fichiers_base', 'di_view_product_resserre_tree')

        if self.di_to_date:
            context.update(di_date_to=self.di_to_date)                
            domain="[('type','!=','service')]"         

        views = [
            (tree_view_id, 'tree'),     
        ]
        return {
            'name': _('Resserre après vente détaillée'),
            'context': context,
            'domain':domain,
            'view_type': 'form',
            "view_mode": 'tree',
            'res_model': 'product.product',
            'type': 'ir.actions.act_window',
            'views': views,
            'view_id': False,
            'search_view_id': search_view_id,
        }
