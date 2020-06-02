
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
    di_liste_comptage = fields.Boolean("Liste de comptage", default=False)
    di_masquer_ventes = fields.Boolean("Masquer les ventes", default=False)
    
    @api.multi
    def imprimer_resserre(self):
        context = dict(self.env.context or {})
        context.update(di_aff_ven=self.di_masquer_ventes)
        context.update(di_aff_pertes=True)
        context.update(di_liste_comptage=self.di_liste_comptage)
        if self.di_to_date:
            context.update(di_date_to=self.di_to_date) 
        self.di_product_ids = self.env['product.product'].search(['&', ('type', '!=', 'service'), '|', '|', ('qty_available', '>', 0.0), ('qty_available', '<', 0.0), ('di_flg_avec_ventes', '=', True)])
        
#         domain="['&',('type','=','product'),'|',('qty_available','>',0.0),('qty_available','<',0.0)]"
            
        
        
        if self.di_liste_comptage or self.di_masquer_ventes:
            return self.env.ref('difodoo_fichiers_base.di_action_report_resserre_portrait').report_action(self)
        else:                                            
            return self.env.ref('difodoo_fichiers_base.di_action_report_resserre').report_action(self)
            
                                                          
class DiImpRessTbWiz(models.TransientModel):
    _name = "di.imp.ress.tb.wiz"
    _description = "Wizard d'impression de la resserre"        
 
    di_resserre_ids = fields.Many2many("di.resserre")
    
    di_liste_comptage = fields.Boolean("Liste de comptage", default=False)
    di_masquer_ventes = fields.Boolean("Masquer les ventes", default=False)
    
    @api.multi
    def imprimer_resserre(self):
        
        query_args = {'product_id': id}    
                       
        query = """ select id  from di_resserre order by date desc  limit 1 """            
        self.env.cr.execute(query, query_args)                                                 
    
        try: 
            result = self.env.cr.fetchall()[0] 
            id_dern_ress = result[0] and result[0] or False
        except:
            id_dern_ress=False   
        if id_dern_ress :    
            dern_ress = self.env['di.resserre'].browse(id_dern_ress)
        else:
            dern_ress=False
            
        if dern_ress:
            date= dern_ress.date
        else:
            date=False
       
        if date:
            self.di_resserre_ids = self.env['di.resserre'].search([('date', '=', date)])
        
#         domain="['&',('type','=','product'),'|',('qty_available','>',0.0),('qty_available','<',0.0)]"
            
        
        if self.di_resserre_ids:
            if self.di_liste_comptage or self.di_masquer_ventes:
                return self.env.ref('difodoo_fichiers_base.di_action_report_resserre_tb_portrait').report_action(self)
            else:                                            
                return self.env.ref('difodoo_fichiers_base.di_action_report_resserre_tb').report_action(self)
        else:
            return self.env['di.popup.wiz'].afficher_message("Pas de resserre générée.",True,False,False,False)
            
    
