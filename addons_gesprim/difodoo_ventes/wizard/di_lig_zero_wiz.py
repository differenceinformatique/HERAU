# -*- coding: utf-8 -*-
from odoo import api, fields, models
from datetime import date, timedelta, datetime
from odoo.exceptions import ValidationError

class DiLigZeroWiz(models.TransientModel):
    _name = "di.lig.zero.wiz"
    _description = "Wizard de suppression des lignes à zéro"
    
    order_id = fields.Many2one("sale.order", string="Commande")        
    lines = fields.Many2many("sale.order.line", string="Lignes")
    
    @api.multi
    def di_supp_lig_zero(self):
        self.order_id.write({'order_line': [(2, line.id, False) for line in self.lines]})

    @api.model
    def default_get(self, fields):
        res = super(DiLigZeroWiz, self).default_get(fields)             
        res['order_id']=self.env.context(['order_id'])
        res['lines']=self.env.context(['lines'])                    
        return res    