# -*- coding: utf-8 -*-
from odoo import osv
from odoo.exceptions import Warning
from odoo import models, fields, api
from xlrd.formula import FMLA_TYPE_COND_FMT

class ResPartner(models.Model):
     _inherit = "res.partner"

     di_siret = fields.Char(string="N° siret")
     #référencement article 
     di_refarticle_ids = fields.Many2many('product.product', 'di_referencement_article_tiers', 'partner_id','product_id', string='Référencement article')
          