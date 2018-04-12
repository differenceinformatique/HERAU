
# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
    
class DiOrigine(models.Model):
    _name = "di.origine"
    _description = "Origine"
    _order = "name"
    
    di_company_id = fields.Many2one('res.company', string='Société', readonly=True,  default=lambda self: self.env.user.company_id)         
    di_des = fields.Char(string="Désignation", required=True)
    name = fields.Char(string="Code", required=True)