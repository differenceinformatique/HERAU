# -*- coding: utf-8 -*-
from odoo import models, fields, api

class DiInheritedSaleOrderLine(models.Model):
    _inherit = "sale.order.line"
    
    di_qte_un_saisie    = fields.Float(string='Quantité en unité de saisie')
    di_un_saisie        = fields.Selection([("PIECE", "Pièce"), ("COLIS", "Colis"),("PALETTE", "Palette"),("POIDS","Poids")], string="Unité de saisie")
    di_type_palette     = fields.Many2one('product.packaging', string='Palette') 
    di_nb_pieces        = fields.Integer(string='Nb pièces')
    di_nb_colis         = fields.Integer(string='Nb colis')
    di_nb_palette       = fields.Float(string='Nb palettes')
    di_poin          = fields.Float(string='Poids net')
    di_poib          = fields.Float(string='Poids brut')
    di_tare          = fields.Float(string='Tare')
    
    
    @api.multi
    @api.onchange('product_id')
    def _di_charger_valeur_par_defaut(self):
        if self.product_id != False:
            self.di_un_saisie = self.product_id.di_un_saisie
            self.di_type_palette = self.product_id.di_type_palette
            self.product_packaging = self.product_id.di_type_colis
    
    @api.multi
    @api.onchange('di_qte_un_saisie', 'di_un_saisie','di_type_palette','di_nb_poib','di_nb_tare','product_packaging')
    def _di_recalcule_quantites(self):
        if self.di_un_saisie == "PIECE":
            self.di_nb_pieces = self.di_qte_un_saisie
            self.product_uom_qty = self.product_id.di_get_type_piece().qty * self.di_nb_pieces
            if self.product_packaging.qty != 0.0 :
                self.di_nb_colis = self.product_uom_qty / self.product_packaging.qty
            else:      
                self.di_nb_colis = self.product_uom_qty             
            if self.di_type_palette.di_qte_cond_inf != 0.0:
                self.di_nb_palette = self.di_nb_colis / self.di_type_palette.di_qte_cond_inf
            else:
                self.di_nb_palette = self.di_nb_colis
            self.di_poin = self.product_uom_qty * self.product_id.weight 
            self.di_poib = self.di_poin + self.di_tare
                  
        elif self.di_un_saisie == "COLIS":
            self.di_nb_colis = self.di_qte_un_saisie
            self.product_uom_qty = self.product_packaging.qty * self.di_nb_colis
            self.di_nb_pieces = self.product_packaging.di_qte_cond_inf * self.di_nb_colis
            if self.di_type_palette.di_qte_cond_inf !=0.0:                
                self.di_nb_palette = self.di_nb_colis / self.di_type_palette.di_qte_cond_inf
            else:
                self.di_nb_palette = self.di_nb_colis
            self.di_poin = self.product_uom_qty * self.product_id.weight 
            self.di_poib = self.di_poin + self.di_tare
                                 
        elif self.di_un_saisie == "PALETTE":            
            self.di_nb_palette = self.di_qte_un_saisie
            if self.di_type_palette.di_qte_cond_inf!=0.0:
                self.di_nb_colis = self.di_nb_palette / self.di_type_palette.di_qte_cond_inf
            else:
                self.di_nb_colis = self.di_nb_palette
            self.di_nb_pieces = self.product_packaging.di_qte_cond_inf * self.di_nb_colis
            self.product_uom_qty = self.product_packaging.qty * self.di_nb_colis
            self.di_poin = self.product_uom_qty * self.product_id.weight 
            self.di_poib = self.di_poin + self.di_tare
            
        elif self.di_un_saisie == "POIDS":
            self.di_poin = self.di_qte_un_saisie
            self.di_poib = self.di_poin + self.di_tare
            self.product_uom_qty = self.di_poin
            if self.product_packaging.qty !=0.0:
                self.di_nb_colis = self.product_uom_qty / self.product_packaging.qty
            else:
                self.di_nb_colis = self.product_uom_qty
            if self.di_type_palette.di_qte_cond_inf !=0.0:    
                self.di_nb_palette = self.di_nb_colis / self.di_type_palette.di_qte_cond_inf
            else:  
                self.di_nb_palette = self.di_nb_colis
            self.di_nb_pieces = self.product_packaging.di_qte_cond_inf * self.di_nb_colis
            
        else:
            self.di_poin = self.di_qte_un_saisie
            self.di_poib = self.di_poin + self.di_tare
            self.product_uom_qty = self.di_poin
            if self.product_packaging.qty !=0.0:
                self.di_nb_colis = self.product_uom_qty / self.product_packaging.qty
            else:
                self.di_nb_colis = self.product_uom_qty
            if self.di_type_palette.di_qte_cond_inf !=0.0:    
                self.di_nb_palette = self.di_nb_colis / self.di_type_palette.di_qte_cond_inf
            else:  
                self.di_nb_palette = self.di_nb_colis
            self.di_nb_pieces = self.product_packaging.di_qte_cond_inf * self.di_nb_colis