# # -*- coding: utf-8 -*-
#   
# from odoo import api, fields, models, _
#      
# class DiSaleTaxe(models.Model):
#     _name = "di.sale.taxe"
#     _description = "Taxes sur commande de vente"
#     _order = "name"
#      
#     company_id = fields.Many2one('res.company', string='Société', readonly=True,  default=lambda self: self.env.user.company_id)                 
#     name = fields.Char(string="Taxe")
#     order_id = fields.Many2one('sale.order', string='Commande', required=True, ondelete='cascade', index=True, copy=False, readonly=True)
#     amount = fields.Float("Montant taxe")
#     base = fields.Float("Base taxe")
#      