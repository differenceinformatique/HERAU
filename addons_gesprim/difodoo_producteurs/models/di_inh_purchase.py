# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, float_compare
from datetime import datetime, timedelta
from odoo.exceptions import UserError
from ...difodoo_fichiers_base.controllers import di_ctrl_print
from odoo.addons import decimal_precision as dp

# from difodoo.addons_gesprim.difodoo_ventes.models import di_inherited_stock_move 


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"    
    
    di_categorie_id = fields.Many2one("di.categorie",string="Catégorie")    
    di_categorie_di_des = fields.Char(related='di_categorie_id.di_des')#, store='False')
    
    di_origine_id = fields.Many2one("di.origine",string="Origine")
    di_origine_di_des = fields.Char(related='di_origine_id.di_des')#, store='False')
    
    di_marque_id = fields.Many2one("di.marque",string="Marque")
    di_marque_di_des = fields.Char(related='di_marque_id.di_des')#, store='False')
    
    di_calibre_id = fields.Many2one("di.calibre",string="Calibre")
    di_calibre_di_des = fields.Char(related='di_calibre_id.di_des')#, store='False')
    
    @api.multi
    @api.depends('di_qte_un_saisie', 'di_un_saisie', 'di_type_palette_id', 
                 'di_nb_pieces', 'di_nb_colis', 'di_nb_palette', 
                 'di_poin', 'di_poib', 'di_tare','product_packaging','di_categorie_id', 
                 'di_origine_id', 'di_marque_id', 'di_calibre_id')
    def _di_modif_champs_bl(self):  
        for pol in self: 
            moves = self.env['stock.move'].search([('purchase_line_id', '=', pol.id)])
            for move in moves:  
                move.di_qte_un_saisie_init = pol.di_qte_un_saisie
                move.di_un_saisie_init = pol.di_un_saisie
                move.di_type_palette_init_id = pol.di_type_palette_id
                move.di_nb_pieces_init = pol.di_nb_pieces
                move.di_nb_colis_init = pol.di_nb_colis
                move.di_nb_palette_init = pol.di_nb_palette
                move.di_poin_init = pol.di_poin
                move.di_poib_init = pol.di_poib
                move.di_tare_init = pol.di_tare
                move.di_product_packaging_init_id = pol.product_packaging
                move.di_categorie_id = pol.di_categorie_id
                move.di_origine_id = pol.di_origine_id
                move.di_marque_id = pol.di_marque_id
                move.di_calibre_id = pol.di_calibre_id       
    
    @api.multi
    @api.onchange('product_id')
    def _di_charger_valeur_par_defaut(self):
        super(PurchaseOrderLine, self)._di_charger_valeur_par_defaut()
        if self.ensure_one():
            if self.partner_id and self.product_id:
                ref = self.env['di.ref.art.tiers'].search([('di_partner_id','=',self.partner_id.id),('di_product_id','=',self.product_id.id)],limit=1)
            else:
                ref = False
            if ref:                        
                self.di_categorie_id = self.product_id.di_categorie_id 
                self.di_origine_id = self.product_id.di_origine_id 
                self.di_marque_id = self.product_id.di_marque_id 
                self.di_calibre_id = self.product_id.di_calibre_id                                               
            else:
                if self.product_id:                                    
                    self.di_categorie_id = self.product_id.di_categorie_id 
                    self.di_origine_id = self.product_id.di_origine_id 
                    self.di_marque_id = self.product_id.di_marque_id 
                    self.di_calibre_id = self.product_id.di_calibre_id 
        