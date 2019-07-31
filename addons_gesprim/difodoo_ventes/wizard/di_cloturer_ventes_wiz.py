# -*- coding: utf-8 -*-
from odoo import api, fields, models
from datetime import timedelta, datetime
import io
# import os
import base64
# from ..models import di_outils
# from pip._internal import download
from odoo.tools import pycompat

class DiCloturerVentes(models.TransientModel):
    _name = "di.cloturer.ventes.wiz"
    _description = "Wizard clôture des ventes"
    
    date_cloture = fields.Date('Date clôture', help="Date jusqu'à laquelle les ventes ne seront plus prises en compte dans l'impression de la resserre.", default=datetime.today().date())
  
    @api.multi
    def cloturer_ventes(self):
        self.ensure_one()  
        
        smlines = self.env['stock.move.line'].search(['&', ('di_flg_cloture', '=', False), ('state', '=', 'done'), ('di_usage_loc', '=', 'internal'), ('di_usage_loc_dest', 'in', ('customer','inventory'))]).filtered(lambda l: l.date.date() <= self.date_cloture)
        
        
        smlines.update({
                'di_flg_cloture': True,               
            })    
        
        articles=smlines.mapped('product_id')
        articles.update({
                'di_flg_avec_ventes': False,
            })
        
        smlines = self.env['stock.move.line'].search(['&', ('di_flg_cloture', '=', False), ('state', '=', 'done'), ('di_usage_loc', '=', 'customer'), ('di_usage_loc_dest', '=', 'internal')]).filtered(lambda l: l.date.date() <= self.date_cloture)
        
        
        smlines.update({
                'di_flg_cloture': True,               
            })    
        articles=smlines.mapped('product_id')
        articles.update({
                'di_flg_avec_ventes': False,
            })
        return smlines                    
