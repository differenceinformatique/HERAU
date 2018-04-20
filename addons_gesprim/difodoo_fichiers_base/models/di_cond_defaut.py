# -*- coding: utf-8 -*-
 
from odoo import api, fields, models, _
    
class DiCondDefaut(models.Model):
    _name = "di.conddefaut"
    _description = "Conditionnement par d�faut"
    _order = "name"
    
    di_company_id = fields.Many2one('res.company', string='Société', readonly=True,  default=lambda self: self.env.user.company_id)             
    di_des = fields.Char(string="Désignation", required=True)
    name = fields.Char(string="Code", required=True)
    di_type_cond = fields.Selection([("PIECE", "Cond. Réf."), ("COLIS", "Colis"),("PALETTE", "Palette")], string="Type de conditionnement")    