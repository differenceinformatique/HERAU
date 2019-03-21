
# -*- coding: utf-8 -*-

from odoo import api, fields, models
from datetime import date, timedelta, datetime
from odoo.exceptions import ValidationError
import time


class DiImpRessWiz(models.TransientModel):
    _name = "di.imp.ress.wiz"
    _description = "Wizard d'impression de la resserre"        
 
    di_product_ids = fields.Many2many("product.product")
    di_to_date = fields.Date('Le', default=time.strftime('%Y-%m-%d') )
    
    @api.multi
    def imprimer_resserre(self):
        context = dict(self.env.context or {})
        if self.di_to_date:
            context.update(di_date_to=self.di_to_date) 
        self.di_product_ids=self.env['product.product'].search([('type','!=','service')]).with_context(context)  
        
        
                                                    
        return self.env.ref('difodoo_fichiers_base.di_action_report_resserre').report_action(self)                                                      
    