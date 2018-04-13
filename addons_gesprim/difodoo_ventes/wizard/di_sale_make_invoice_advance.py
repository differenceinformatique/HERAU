# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import time

from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError

class SaleAdvancePaymentInv(models.TransientModel):
    _inherit = "sale.advance.payment.inv"
#     
#     @api.multi
#     def create_invoices(self):
#         if self.advance_payment_method == 'delivered' or  self.advance_payment_method == 'all':
#             sale_orders = self.env['sale.order'].browse(self._context.get('active_ids', []))
#             res = []
#             for order in sale_orders.sorted(key=lambda so: so.partner_id):
#                 res.append(order)
# 
# #             if self.advance_payment_method == 'delivered':
# #                 sale_orders.action_invoice_create()
# #             elif self.advance_payment_method == 'all':
# #                 sale_orders.action_invoice_create(final=True)
# #         else:
# #             # gestions des acomptes             
# #             resSuper = super(SaleAdvancePaymentInv, self).create_invoices()
# #             return resSuper
# #         return {'type': 'ir.actions.act_window_close'}
