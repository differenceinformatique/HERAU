
# -*- coding: utf-8 -*-

from odoo import api, fields, models
from datetime import date, timedelta, datetime
from odoo.exceptions import ValidationError


class DiImpRessWiz(models.TransientModel):
    _name = "di.imp.ress.wiz"
    _description = "Wizard d'impression de la resserre"        
 
    di_product_ids = fields.Many2many("product.product")
    
    
    @api.multi
    def imprimer_resserre(self):
        
        self.di_product_ids=self.env['product.product'].search([])  
                                                       
        return self.env.ref('difodoo_fichiers_base.di_action_report_resserre').report_action(self)                                                       
    