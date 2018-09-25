# -*- coding: utf-8 -*-

from odoo import osv
from odoo.exceptions import Warning
from odoo import models, fields, api
from xlrd.formula import FMLA_TYPE_COND_FMT
from suds import null
from odoo.tools.float_utils import float_round

class ProductTemplate(models.Model):
    _inherit = "product.template"    
    
    di_cons = fields.Boolean(string='Emballage consigné',default=False,store=True)