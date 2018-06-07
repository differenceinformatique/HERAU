# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import tools
from odoo import fields, models


class AccountInvoiceReport(models.Model):
    _inherit = "account.invoice.report"
# 
#     #carrier_name = fields.Char('Carrier Name', readonly=True)
#     caliber_name = fields.Char('Caliber Name', readonly=True)
#     packaging_name = fields.Char('Packaging Name', readonly=True)
#     carrier_id = fields.Many2one('delivery.carrier',string = 'Carrier', readonly=True) 
#     #caliber_id = fields.Many2one('hubi.family', string='Caliber', domain=[('level', '=', 'Caliber')], help="The Caliber of the product.", store=False)
#     #packaging_id = fields.Many2one('hubi.family', string='Packaging', domain=[('level', '=', 'Packaging')], help="The Packaging of the product.", store=False)
#     weight_total = fields.Float(string='Total Weight', readonly=True)
#     price_weight = fields.Float(string='Price Weight', group_operator='avg', readonly=True)
#     category_partner = fields.Char('Category Partner', readonly=True)
#     
# 
#     def _select(self):
#         #return super(HubiAccountInvoiceReport, self)._select()
#         return super(HubiAccountInvoiceReport, self)._select() + """,sub.carrier_id AS carrier_id, 
#                 sub.caliber_name AS caliber_name, sub.packaging_name AS packaging_name, 
#                 sub.category_partner AS category_partner, sub.weight_total AS weight_total,
#                 sub.price_weight as price_weight"""
# 
#     def _sub_select(self):
#         #return super(HubiAccountInvoiceReport, self)._sub_select()
#         return super(HubiAccountInvoiceReport, self)._sub_select() + """,ai.carrier_id AS carrier_id,  
#                 hfc.name AS caliber_name, hfp.name AS packaging_name, 
#                 
#                 (SELECT min(rpc.name)  FROM res_partner_category rpc 
#                     LEFT JOIN res_partner_res_partner_category_rel cat ON  ai.commercial_partner_id =cat.partner_id
#                     WHERE (cat.category_id = rpc.id  AND rpc.parent_id is not null ) ) AS category_partner 
#                 ,sum(ail.weight) AS weight_total, avg(ail.price_weight) AS price_weight"""
# 
#     def _from(self):
#         #return super(HubiAccountInvoiceReport, self)._from()
#         return super(HubiAccountInvoiceReport, self)._from() + """
#                     LEFT JOIN hubi_family hfc ON (pt.caliber_id = hfc.id)
#                     LEFT JOIN hubi_family hfp ON (pt.packaging_id = hfp.id) 
#                     """
#                     #LEFT JOIN res_partner_res_partner_category_rel cat ON  ai.commercial_partner_id =cat.partner_id 
#                     #LEFT JOIN res_partner_category rpc ON (cat.category_id = rpc.id  AND rpc.parent_id is not null)
#                     
#     def _group_by(self):
#         #return super(HubiAccountInvoiceReport, self)._group_by()
#         return super(HubiAccountInvoiceReport, self)._group_by() + ", ai.carrier_id, hfc.name, hfp.name"
