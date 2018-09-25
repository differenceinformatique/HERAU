
# -*- coding: utf-8 -*-

from odoo.exceptions import Warning
from odoo import models, fields, api

class ResPartner(models.Model):
    _inherit = "res.partner"
 
    di_is_court = fields.Boolean(string='Est un metteur en marche', default=False, help=""" Le tiers est un metteur en marche et peut donc recevoir des commissions """)  # modif attribut default
    di_prc_com_avec_court = fields.Float(string='% commission',help="""Pourcentage de commission que le metteur en marche récupère sur une vente. """, default=0.0)    