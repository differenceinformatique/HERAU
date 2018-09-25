# -*- coding: utf-8 -*-
 
from odoo import api, fields, models, _

    
class DiParam(models.Model):
    _inherit = "di.param" 
   
    di_prc_com_avec_court = fields.Float(string='% commission OP avec metteur en marché ',help="""Pourcentage de commission que prendra l'OP sur la ligne si un metteur en marche a fait la vente. """, default=0.0)
    di_prc_com_sans_court = fields.Float(string='% commission OP sans metteur en marché',help="""Pourcentage de commission que prendra l'OP sur la ligne si l'OP a fait la vente directe. """, default=0.0)    
    di_art_com  =   fields.Many2one('product.product',string="Article commission",help="""Article qui va servir pour la facturation des commissions. """)              