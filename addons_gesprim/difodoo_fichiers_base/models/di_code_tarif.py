# -*- coding: utf-8 -*-
 
from odoo import api, fields, models, _
    
class DiCodeTarif(models.Model):
    _name = "di.code.tarif"
    _description = "Code tarif"
    _order = "name"
    
    name = fields.Char(string="Code", required=True)
    di_company_id = fields.Many2one('res.company', string='Société', readonly=True,  default=lambda self: self.env.user.company_id)             
    di_des = fields.Char(string="Désignation", required=True)    
    di_coef = fields.Float(string="Coefficient multiplicateur tarif achat", default=0.0)