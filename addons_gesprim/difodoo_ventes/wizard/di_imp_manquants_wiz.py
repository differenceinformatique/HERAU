
# -*- coding: utf-8 -*-

from odoo import api, fields, models
from datetime import date, timedelta, datetime
from odoo.exceptions import ValidationError


class DiImpManqWiz(models.TransientModel):
    _name = "di.imp.manq.wiz"
    _description = "Wizard d'impression des manquants"
    
    di_company_id = fields.Many2one('res.company', string='Société', readonly=True,  default=lambda self: self.env.user.company_id)
          
    di_sol_ids = fields.Many2many("sale.order.line")
    
    
    @api.multi
    def imprimer_manquants(self):  
        lines = self.env['sale.order.line'].search(['&',('state', 'in', ('draft','sent','sale')),('invoice_status','=','no')]).filtered(lambda s: s.order_id.invoice_status == 'no').sorted(key=lambda s: s.order_id)
        
        for line in lines:
            if line.product_id.qty_available < line.product_id.di_get_qte_cde():
                self.di_sol_ids = self.di_sol_ids + line                                                          
        return self.env.ref('difodoo_ventes.di_action_report_manquants').report_action(self)                                                       
            
    @api.model
    def default_get(self, fields):
        res = super(DiImpManqWiz, self).default_get(fields)       
                                                                              
        return res    
