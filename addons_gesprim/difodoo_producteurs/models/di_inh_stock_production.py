# -*- coding: utf-8 -*-
from odoo import fields, models
class ProductionLot(models.Model):
    _inherit = "stock.production.lot"
    di_plus_suivi = fields.Boolean(string='Ne plus suivre', default=False, help="""Champ permettant de ne plus suivre un numéro de série pour un article de type 'emballage consigné'.""", store=True)