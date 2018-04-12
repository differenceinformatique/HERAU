
# -*- coding: utf-8 -*-

from odoo import api, fields, models
from datetime import date, timedelta, datetime
from odoo.exceptions import ValidationError


class DiSaisieDefCodeWiz(models.TransientModel):
    _name = "di.saisie.code.wiz"
    _description = "Wizard de saisie du default code"
     
    code = fields.Char('Code', index=True, copy=False)
        
    
    @api.multi
    def valider_code(self):                                                                       
        return self.code                                                       
            
    @api.model
    def default_get(self, fields):
        res = super(DiSaisieDefCodeWiz, self).default_get(fields)                                                                                       
        return res    