
# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, float_compare
from datetime import datetime, timedelta
from odoo.exceptions import UserError
from ...difodoo_fichiers_base.controllers import di_ctrl_print
import ctypes
from math import ceil
from odoo.addons import decimal_precision as dp
from difodoo.addons_gesprim.difodoo_fichiers_base.models import di_param


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"
    
    di_categorie_id = fields.Many2one("di.categorie",string="Catégorie")    
    di_categorie_di_des = fields.Char(related='di_categorie_id.di_des')#, store='False')
    
    di_origine_id = fields.Many2one("di.origine",string="Origine")
    di_origine_di_des = fields.Char(related='di_origine_id.di_des')#, store='False')
    
    di_marque_id = fields.Many2one("di.marque",string="Marque")
    di_marque_di_des = fields.Char(related='di_marque_id.di_des')#, store='False')
    
    di_calibre_id = fields.Many2one("di.calibre",string="Calibre")
    di_calibre_di_des = fields.Char(related='di_calibre_id.di_des')#, store='False')
    
    di_station_id = fields.Many2one("stock.location",string="Station")
    di_station_di_des = fields.Char(related='di_station_id.name')#, store='False')
    
    di_courtier_id = fields.Many2one("res.partner",string="Metteur en marche")
    di_prc_com_court = fields.Float(string='% com. Metteur en marche',help="""Pourcentage de commission que le metteur en marche récupère sur la vente. """, default=0.0,store=True)
    di_prc_com_OP = fields.Float(string='% com. OP',help="""Pourcentage de commission que l'OP récupère sur la vente. """, default=0.0,store=True)#,compute='_di_compute_com_op')
    
    di_flg_com = fields.Boolean(string='Commission payée',default=False,help="""Flag permettant de savoir si la commission de cette ligne a déjà été payée au courtier ou non.""")
    
        
    @api.onchange('product_id')
    def _di_charger_prc_op(self):   
        if self.di_prc_com_OP == 0.0:
            param = self.env['di.param'].search([('di_company_id','=',self.env.user.company_id.id)])
            if self.di_courtier_id:
                if self.di_courtier_id.di_is_court:
                    self.di_prc_com_OP = param.di_prc_com_avec_court
                else:
                    self.di_prc_com_OP = param.di_prc_com_sans_court
            else:
                self.di_prc_com_OP = param.di_prc_com_sans_court
                
    @api.onchange('di_courtier_id')
    def _di_charger_prc_court(self):
        param = self.env['di.param'].search([('di_company_id','=',self.env.user.company_id.id)])
        if self.di_courtier_id:            
            if self.di_courtier_id.di_is_court:
                self.di_prc_com_OP = param.di_prc_com_avec_court
                self.di_prc_com_court = self.di_courtier_id.di_prc_com_avec_court
            else:
                self.di_prc_com_court = 0.0
                self.di_prc_com_OP = param.di_prc_com_sans_court
        else:
            self.di_prc_com_court = 0.0   
            self.di_prc_com_OP = param.di_prc_com_sans_court                      


    @api.multi
    @api.depends('di_marge_prc','company_id.di_param_id.di_seuil_marge_prc')#,'di_param_id.di_seuil_marge_prc')
    def _di_compute_marge_seuil(self):   
        for sol in self:
            if sol.di_marge_prc < sol.company_id.di_param_id.di_seuil_marge_prc:     
                sol.di_marge_inf_seuil = True
            else:
                sol.di_marge_inf_seuil = False
           
               
    @api.multi
    @api.onchange('product_id')
    def _di_charger_valeur_par_defaut(self):
        super(SaleOrderLine, self)._di_charger_valeur_par_defaut()
        if self.ensure_one():
            if self.order_partner_id and self.product_id:
                ref = self.env['di.ref.art.tiers'].search([('di_partner_id','=',self.order_partner_id.id),('di_product_id','=',self.product_id.id)],limit=1)
            else:
                ref = False
            if ref:                    
                self.di_categorie_id = self.product_id.di_categorie_id 
                self.di_origine_id = self.product_id.di_origine_id 
                self.di_marque_id = self.product_id.di_marque_id 
                self.di_calibre_id = self.product_id.di_calibre_id                               
                self.di_station_id = ref.di_station_id 
            else:
                if self.product_id:                            
                    self.di_categorie_id = self.product_id.di_categorie_id 
                    self.di_origine_id = self.product_id.di_origine_id 
                    self.di_marque_id = self.product_id.di_marque_id 
                    self.di_calibre_id = self.product_id.di_calibre_id 
                    self.di_station_id = self.product_id.di_station_id     
           