# -*- coding: utf-8 -*-
from odoo import models, fields, api

class DiInheritedStockMove(models.Model):
    _inherit = "stock.move"
    
    di_qte_un_saisie = fields.Float(string='Quantité en unité de saisie')
    di_un_saisie = fields.Selection([("PIECE", "Pièce"), ("COLIS", "Colis"), ("PALETTE", "Palette"), ("POIDS", "Poids")], string="Unité de saisie")
    di_type_palette = fields.Many2one('product.packaging', string='Palette') 
    di_nb_pieces = fields.Integer(string='Nb pièces', compute="_compute_qte_aff", store=True)
    di_nb_colis = fields.Integer(string='Nb colis', compute="_compute_qte_aff", store=True)
    di_nb_palette = fields.Float(string='Nb palettes', compute="_compute_qte_aff", store=True)
    di_poin = fields.Float(string='Poids net', compute="_compute_qte_aff", store=True)
    di_poib = fields.Float(string='Poids brut')
    di_tare = fields.Float(string='Tare')
    product_packaging = fields.Many2one('product.packaging', string='Package', default=False)
   
    @api.one
    @api.depends('di_qte_un_saisie', 'di_un_saisie', 'di_type_palette', 'di_poib', 'di_tare', 'product_packaging')
    def _compute_qte_aff(self):
        if self.di_un_saisie == "PIECE":
            self.di_nb_pieces = self.di_qte_un_saisie            
            if self.product_packaging.qty != 0.0 :
                self.di_nb_colis = self.quantity_done / self.product_packaging.qty
            else:      
                self.di_nb_colis = self.quantity_done             
            if self.di_type_palette.di_qte_cond_inf != 0.0:
                self.di_nb_palette = self.di_nb_colis / self.di_type_palette.di_qte_cond_inf
            else:
                self.di_nb_palette = self.di_nb_colis
            self.di_poin = self.quantity_done * self.product_id.weight             
                  
        elif self.di_un_saisie == "COLIS":
            self.di_nb_colis = self.di_qte_un_saisie            
            self.di_nb_pieces = self.product_packaging.di_qte_cond_inf * self.di_nb_colis
            if self.di_type_palette.di_qte_cond_inf != 0.0:                
                self.di_nb_palette = self.di_nb_colis / self.di_type_palette.di_qte_cond_inf
            else:
                self.di_nb_palette = self.di_nb_colis
            self.di_poin = self.quantity_done * self.product_id.weight             
                                 
        elif self.di_un_saisie == "PALETTE":            
            self.di_nb_palette = self.di_qte_un_saisie
            if self.di_type_palette.di_qte_cond_inf != 0.0:
                self.di_nb_colis = self.di_nb_palette / self.di_type_palette.di_qte_cond_inf
            else:
                self.di_nb_colis = self.di_nb_palette
            self.di_nb_pieces = self.product_packaging.di_qte_cond_inf * self.di_nb_colis            
            self.di_poin = self.quantity_done * self.product_id.weight             
            
        elif self.di_un_saisie == "POIDS":
            self.di_poin = self.di_qte_un_saisie                        
            if self.product_packaging.qty != 0.0:
                self.di_nb_colis = self.quantity_done / self.product_packaging.qty
            else:
                self.di_nb_colis = self.quantity_done
            if self.di_type_palette.di_qte_cond_inf != 0.0:    
                self.di_nb_palette = self.di_nb_colis / self.di_type_palette.di_qte_cond_inf
            else:  
                self.di_nb_palette = self.di_nb_colis
            self.di_nb_pieces = self.product_packaging.di_qte_cond_inf * self.di_nb_colis
            
        else:
            self.di_poin = self.di_qte_un_saisie            
            self.quantity_done = self.di_poin
            if self.product_packaging.qty != 0.0:
                self.di_nb_colis = self.quantity_done / self.product_packaging.qty
            else:
                self.di_nb_colis = self.quantity_done
            if self.di_type_palette.di_qte_cond_inf != 0.0:    
                self.di_nb_palette = self.di_nb_colis / self.di_type_palette.di_qte_cond_inf
            else:  
                self.di_nb_palette = self.di_nb_colis
            self.di_nb_pieces = self.product_packaging.di_qte_cond_inf * self.di_nb_colis 
    @api.multi
    @api.onchange('product_id')
    def _di_charger_valeur_par_defaut(self):
        if self.product_id.id != False:
            self.di_un_saisie = self.product_id.di_un_saisie
            self.di_type_palette = self.product_id.di_type_palette
            self.product_packaging = self.product_id.di_type_colis
            
    @api.multi
    @api.onchange('di_qte_un_saisie', 'di_un_saisie', 'di_type_palette', 'di_poib', 'di_tare', 'product_packaging')
    def _di_recalcule_quantites(self):
        if self.di_un_saisie == "PIECE":
            self.di_nb_pieces = self.di_qte_un_saisie
            self.quantity_done = self.product_id.di_get_type_piece().qty * self.di_nb_pieces
            if self.product_packaging.qty != 0.0 :
                self.di_nb_colis = self.quantity_done / self.product_packaging.qty
            else:      
                self.di_nb_colis = self.quantity_done             
            if self.di_type_palette.di_qte_cond_inf != 0.0:
                self.di_nb_palette = self.di_nb_colis / self.di_type_palette.di_qte_cond_inf
            else:
                self.di_nb_palette = self.di_nb_colis
            self.di_poin = self.quantity_done * self.product_id.weight 
            self.di_poib = self.di_poin + self.di_tare
                  
        elif self.di_un_saisie == "COLIS":
            self.di_nb_colis = self.di_qte_un_saisie
            self.quantity_done = self.product_packaging.qty * self.di_nb_colis
            self.di_nb_pieces = self.product_packaging.di_qte_cond_inf * self.di_nb_colis
            if self.di_type_palette.di_qte_cond_inf != 0.0:                
                self.di_nb_palette = self.di_nb_colis / self.di_type_palette.di_qte_cond_inf
            else:
                self.di_nb_palette = self.di_nb_colis
            self.di_poin = self.quantity_done * self.product_id.weight 
            self.di_poib = self.di_poin + self.di_tare
                                 
        elif self.di_un_saisie == "PALETTE":            
            self.di_nb_palette = self.di_qte_un_saisie
            if self.di_type_palette.di_qte_cond_inf != 0.0:
                self.di_nb_colis = self.di_nb_palette / self.di_type_palette.di_qte_cond_inf
            else:
                self.di_nb_colis = self.di_nb_palette
            self.di_nb_pieces = self.product_packaging.di_qte_cond_inf * self.di_nb_colis
            self.quantity_done = self.product_packaging.qty * self.di_nb_colis
            self.di_poin = self.quantity_done * self.product_id.weight 
            self.di_poib = self.di_poin + self.di_tare
            
        elif self.di_un_saisie == "POIDS":
            self.di_poin = self.di_qte_un_saisie
            self.di_poib = self.di_poin + self.di_tare
            self.quantity_done = self.di_poin
            if self.product_packaging.qty != 0.0:
                self.di_nb_colis = self.quantity_done / self.product_packaging.qty
            else:
                self.di_nb_colis = self.quantity_done
            if self.di_type_palette.di_qte_cond_inf != 0.0:    
                self.di_nb_palette = self.di_nb_colis / self.di_type_palette.di_qte_cond_inf
            else:  
                self.di_nb_palette = self.di_nb_colis
            self.di_nb_pieces = self.product_packaging.di_qte_cond_inf * self.di_nb_colis
            
        else:
            self.di_poin = self.di_qte_un_saisie
            self.di_poib = self.di_poin + self.di_tare
            self.quantity_done = self.di_poin
            if self.product_packaging.qty != 0.0:
                self.di_nb_colis = self.quantity_done / self.product_packaging.qty
            else:
                self.di_nb_colis = self.quantity_done
            if self.di_type_palette.di_qte_cond_inf != 0.0:    
                self.di_nb_palette = self.di_nb_colis / self.di_type_palette.di_qte_cond_inf
            else:  
                self.di_nb_palette = self.di_nb_colis
            self.di_nb_pieces = self.product_packaging.di_qte_cond_inf * self.di_nb_colis
              
    @api.model
    def create(self, vals):               
#         DiStockMove = self.env['stock.move']
#         for DiStockMove in self:
        di_avec_sale_line_id = False  # initialisation d'une variable       
        di_ctx = dict(self._context or {})  # chargement du contexte
        for key in vals.items():  # vals est un dictionnaire qui contient les champs modifiés, on va lire les différents enregistrements                      
            if key[0] == "sale_line_id":  # si on a modifié sale_line_id
                di_avec_sale_line_id = True
        if di_avec_sale_line_id == True:
            if vals["sale_line_id"] != False and  vals["sale_line_id"] != 0 :  # si on a bien un sale_line_id 
                # recherche de l'enregistrement sale order line avec un sale_line_id = sale_line_id
                Disaleorderline = self.env['sale.order.line'].search([('id', '=', vals["sale_line_id"])], limit=1)            
                if Disaleorderline.id != False:                    
                    vals["di_qte_un_saisie"] = Disaleorderline.di_qte_un_saisie
                    vals["di_un_saisie"] = Disaleorderline.di_un_saisie
                    vals["di_type_palette"] = Disaleorderline.di_type_palette.id
                    vals["di_nb_colis"] = Disaleorderline.di_nb_colis
                    vals["di_nb_pieces"] = Disaleorderline.di_nb_pieces
                    vals["di_nb_palette"] = Disaleorderline.di_nb_palette
                    vals["di_poin"] = Disaleorderline.di_poin
                    vals["di_poib"] = Disaleorderline.di_poib
                    vals["di_tare"] = Disaleorderline.di_tare
                    vals["product_packaging"] = Disaleorderline.product_packaging.id     
#         else:
#             vals["di_nb_colis"] = Disaleorderline.di_nb_colis
#             vals["di_nb_pieces"] = Disaleorderline.di_nb_pieces
#             vals["di_nb_palette"] = Disaleorderline.di_nb_palette
#             vals["di_poin"] = Disaleorderline.di_poin
        res = super(DiInheritedStockMove, self).create(vals)                           
        return res
    
#    stock_move_obj self.pool.get('stock.move')
# sale_lines = [ move.procurement_id.sale_line_id for move in stock_move_obj.browse(cr, uid, move_ids) if move.procurement_id and move.procurement_id.sale_line_id] 
# 
# print "Browse record of Associated Sale Order LIne",sale_lines 
# 
# #If you want Sale order line ids only. than
# 
# sale_line_ids = [ move.procurement_id.sale_line_id.id for move in stock_move_obj.browse(cr, uid, move_ids) if move.procurement_id and move.procurement_id.sale_line_id]  
# 
# print " Sale Line IDs:::::",sale_line_ids
