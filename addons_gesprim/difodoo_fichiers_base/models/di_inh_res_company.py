# -*- coding: utf-8 -*-

from odoo.exceptions import Warning
from odoo import models, fields, api

class ResCompany(models.Model):
    _inherit = "res.company"
    
    di_param_id = fields.One2many('di.param','di_company_id',"Paramètage")    
#     def di_get_di_param(self):
#         return self.env['di.param'].search(['di_company_id','=',id],limit=1)     