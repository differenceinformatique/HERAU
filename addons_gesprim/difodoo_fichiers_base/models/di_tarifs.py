# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
    
class DiTarifs(models.Model):
    _name = "di.tarifs"
    _description = "Tarifs"
    _order = "name"
    
#     name = fields.Char(string="Code", required=True)
    di_company_id = fields.Many2one('res.company', string='Société', readonly=True,  default=lambda self: self.env.user.company_id)             
    di_product_id = fields.Many2one('product.product', string='Article', required=True)    
    di_partner_id = fields.Many2one('res.partner',string="Client")
#     di_un_prix    = fields.Selection([("PIECE", "Pièce"), ("COLIS", "Colis"),("PALETTE", "Palette"),("POIDS","Poids")], string="Unité de prix",store=True)
    di_prix = fields.Float(string="Prix",required=True,default=0.0)