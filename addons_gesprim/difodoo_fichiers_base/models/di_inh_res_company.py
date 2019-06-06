# -*- coding: utf-8 -*-

from odoo.exceptions import Warning
from odoo import models, fields, api
from odoo.addons import decimal_precision as dp

class ResCompany(models.Model):
    _inherit = "res.company"
    
    di_param_id = fields.One2many('di.param','di_company_id',"Paramètage")    
    di_capital = fields.Float(string="Capital",digits=dp.get_precision('Product Price'))
    di_form_jur= fields.Char("Forme juridique")
    di_gln= fields.Char("GLN")
#     def di_get_di_param(self):
#         return self.env['di.param'].search(['di_company_id','=',id],limit=1)     