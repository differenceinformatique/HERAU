# -*- coding: utf-8 -*-
from odoo import models, fields, api

class DiInheritedSaleOrderLine(models.Model):
    _inherit = "sale.order.line"
    
    di_qte_un_saisie    = fields.Float(string='Quantité en unité de saisie')
    di_un_saisie        = fields.Selection([("PIECE", "Pièce"), ("COLIS", "Colis"),("PALETTE", "Palette"),("POIDS","Poids")], string="Unité de saisie")
    di_type_palette     = fields.Many2one('product.packaging', string='Palette') 
    di_nb_pieces        = fields.Integer(string='Nb pièces')
    di_nb_colis         = fields.Integer(string='Nb colis')
    di_nb_palette       = fields.Float(string='Nb palettes')
    di_nb_poin          = fields.Float(string='Poids net')
    di_nb_poib          = fields.Float(string='Poids brut')
    di_nb_tare          = fields.Float(string='Tare')
    # TODO : Faire les fonctions de recalcule des champs