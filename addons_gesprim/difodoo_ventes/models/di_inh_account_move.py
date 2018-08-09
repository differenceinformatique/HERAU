
# -*- coding: utf-8 -*-
from odoo import models, fields, api
 

class AccountMoveLine(models.Model):    
    _inherit = 'account.move.line'
    di_transfere = fields.Boolean(string="Transféré",default=False)