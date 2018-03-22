# -*- coding: utf-8 -*-
from odoo import osv
from odoo.exceptions import Warning
from odoo import models, fields, api
from xlrd.formula import FMLA_TYPE_COND_FMT

class DiRefArtTiers(models.Model):
    _name = "di.referencement.article.tiers"
    _description = "Referencement tiers"
        
    partner_id = fields.One2many('res.partner','id',String='Tiers')
    product_id = fields.One2many('product.product','id',String='Article')
    di_un_saisie        = fields.Selection([("PIECE", "Pièce"), ("COLIS", "Colis"),("PALETTE", "Palette"),("POIDS","Poids")], string="Unité de saisie")
    di_type_palette_id     = fields.Many2one('product.packaging', string='Palette par défaut')   
    di_type_colis_id       = fields.Many2one('product.packaging', string='Colis par défaut')
    di_un_prix      = fields.Selection([("PIECE", "Pièce"), ("COLIS", "Colis"),("PALETTE", "Palette"),("POIDS","Poids")], string="Unité de prix",store=True)
  