# -*- coding: utf-8 -*-
from odoo import models, fields, api
 
class StockMove(models.Model):
    _inherit = "stock.move"
     
    di_qte_un_saisie = fields.Float(string='Quantité en unité de saisie', store=True,compute='_quantity_un_saisie_compute')
    di_un_saisie = fields.Selection([("PIECE", "Pièce"), ("COLIS", "Colis"), ("PALETTE", "Palette"), ("POIDS", "Poids")], string="Unité de saisie", store=True)
    di_type_palette_id = fields.Many2one('product.packaging', string='Palette', store=True) 
    di_nb_pieces = fields.Integer(string='Nb pièces', compute="_compute_qte_aff", store=True)
    di_nb_colis = fields.Integer(string='Nb colis' ,compute="_compute_qte_aff", store=True)
    di_nb_palette = fields.Float(string='Nb palettes' ,compute="_compute_qte_aff", store=True)
    di_poin = fields.Float(string='Poids net' ,compute="_compute_qte_aff", store=True)
    di_poib = fields.Float(string='Poids brut', store=True)
    di_tare = fields.Float(string='Tare', store=True)
    di_product_packaging_id = fields.Many2one('product.packaging', string='Package', default=False, store=True)
     
     
    di_qte_un_saisie_init = fields.Float(related="sale_line_id.di_qte_un_saisie")
    di_un_saisie_init = fields.Selection(related="sale_line_id.di_un_saisie")
    di_type_palette_init_id = fields.Many2one(related="sale_line_id.di_type_palette_id") 
    di_nb_pieces_init = fields.Integer(related="sale_line_id.di_nb_pieces")
    di_nb_colis_init = fields.Integer(related="sale_line_id.di_nb_colis")
    di_nb_palette_init = fields.Float(related="sale_line_id.di_nb_palette")
    di_poin_init = fields.Float(related="sale_line_id.di_poin")
    di_poib_init = fields.Float(related="sale_line_id.di_poib")
    di_tare_init = fields.Float(related="sale_line_id.di_tare")
    di_product_packaging_init_id = fields.Many2one(related="sale_line_id.product_packaging")    
    
    def _action_done(self):
        result = super(StockMove, self)._action_done()
        for line in self.mapped('sale_line_id'):
            line.qty_delivered = line._get_delivered_qty()
            line.di_qte_un_saisie_liv = line._get_qte_un_saisie_liv()
            line.di_nb_pieces_liv     = line._get_nb_pieces_liv()
            line.di_nb_colis_liv      = line._get_nb_colis_liv()
            line.di_nb_palette_liv    = line._get_nb_palettes_liv()
            line.di_poin_liv          = line._get_poin_liv()
            line.di_poib_liv          = line._get_poib_liv()
            dimoves = self.env['stock.move'].search([('sale_line_id', '=', line.id)])
            for dimove in dimoves:                                                    
                line.di_type_palette_liv_id  = dimove.di_type_palette_id
                line.di_un_saisie_liv     = dimove.di_un_saisie
                line.di_product_packaging_liv_id = dimove.di_product_packaging_id
                line.di_tare_liv          = dimove.di_tare
                                   
#             line.di_type_palette_liv  = result.di_type_palette_id
#             line.di_un_saisie_liv     = result.di_un_saisie
#             line.di_product_packaging_liv = result.di_product_packaging_id
#             line.di_tare_liv          = result.di_tare  
     
        return result
     
     
    @api.depends('move_line_ids.di_qte_un_saisie', 'di_un_saisie', 'di_type_palette_id','di_product_packaging_id')
    def _quantity_un_saisie_compute(self):
        #recalcule la quantité en unité de saisie en fonction des ventils
        for move in self:
            for move_line in move._get_move_lines():                
                move.di_qte_un_saisie += move_line.di_qte_un_saisie
 
    @api.one
    @api.depends('di_qte_un_saisie', 'di_un_saisie', 'di_type_palette_id', 'di_poib', 'di_tare', 'di_product_packaging_id')
    def _compute_qte_aff(self):
        #recalcule des quantités non modifiables pour qu'elles soient enregistrées même si on met en readonly dans les masques.        
        if self.di_un_saisie == "PIECE":
            self.di_nb_pieces = self.di_qte_un_saisie            
            if self.di_product_packaging_id.qty != 0.0 :
                self.di_nb_colis = self.quantity_done / self.di_product_packaging_id.qty
            else:      
                self.di_nb_colis = self.quantity_done             
            if self.di_type_palette_id.di_qte_cond_inf != 0.0:
                self.di_nb_palette = self.di_nb_colis / self.di_type_palette_id.di_qte_cond_inf
            else:
                self.di_nb_palette = self.di_nb_colis
            self.di_poin = self.quantity_done * self.product_id.weight             
                    
        elif self.di_un_saisie == "COLIS":
            self.di_nb_colis = self.di_qte_un_saisie            
            self.di_nb_pieces = self.di_product_packaging_id.di_qte_cond_inf * self.di_nb_colis
            if self.di_type_palette_id.di_qte_cond_inf != 0.0:                
                self.di_nb_palette = self.di_nb_colis / self.di_type_palette_id.di_qte_cond_inf
            else:
                self.di_nb_palette = self.di_nb_colis
            self.di_poin = self.quantity_done * self.product_id.weight             
                                   
        elif self.di_un_saisie == "PALETTE":            
            self.di_nb_palette = self.di_qte_un_saisie
            if self.di_type_palette_id.di_qte_cond_inf != 0.0:
                self.di_nb_colis = self.di_nb_palette / self.di_type_palette_id.di_qte_cond_inf
            else:
                self.di_nb_colis = self.di_nb_palette
            self.di_nb_pieces = self.di_product_packaging_id.di_qte_cond_inf * self.di_nb_colis            
            self.di_poin = self.quantity_done * self.product_id.weight             
              
        elif self.di_un_saisie == "POIDS":
            self.di_poin = self.di_qte_un_saisie                        
            if self.di_product_packaging_id.qty != 0.0:
                self.di_nb_colis = self.quantity_done / self.di_product_packaging_id.qty
            else:
                self.di_nb_colis = self.quantity_done
            if self.di_type_palette_id.di_qte_cond_inf != 0.0:    
                self.di_nb_palette = self.di_nb_colis / self.di_type_palette_id.di_qte_cond_inf
            else:  
                self.di_nb_palette = self.di_nb_colis
            self.di_nb_pieces = self.di_product_packaging_id.di_qte_cond_inf * self.di_nb_colis
              
        else:
            self.di_poin = self.di_qte_un_saisie            
            self.quantity_done = self.di_poin
            if self.di_product_packaging_id.qty != 0.0:
                self.di_nb_colis = self.quantity_done / self.di_product_packaging_id.qty
            else:
                self.di_nb_colis = self.quantity_done
            if self.di_type_palette_id.di_qte_cond_inf != 0.0:    
                self.di_nb_palette = self.di_nb_colis / self.di_type_palette_id.di_qte_cond_inf
            else:  
                self.di_nb_palette = self.di_nb_colis
            self.di_nb_pieces = self.di_product_packaging_id.di_qte_cond_inf * self.di_nb_colis
                  
    @api.multi            
    @api.onchange('product_id')
    def _di_charger_valeur_par_defaut(self):
        if self.ensure_one():
            if self.product_id.id != False:
                self.di_un_saisie = self.product_id.di_un_saisie
                self.di_type_palette_id = self.product_id.di_type_palette_id
                self.di_product_packaging_id = self.product_id.di_type_colis
    @api.multi            
    @api.onchange('di_qte_un_saisie', 'di_un_saisie', 'di_type_palette_id', 'di_poib', 'di_tare', 'di_product_packaging_id')
    def _di_recalcule_quantites(self):
        if self.ensure_one():
            if self.di_un_saisie == "PIECE":
                self.di_nb_pieces = self.di_qte_un_saisie
                self.quantity_done = self.product_id.di_get_type_piece().qty * self.di_nb_pieces
                if self.di_product_packaging_id.qty != 0.0 :
                    self.di_nb_colis = self.quantity_done / self.di_product_packaging_id.qty
                else:      
                    self.di_nb_colis = self.quantity_done             
                if self.di_type_palette_id.di_qte_cond_inf != 0.0:
                    self.di_nb_palette = self.di_nb_colis / self.di_type_palette_id.di_qte_cond_inf
                else:
                    self.di_nb_palette = self.di_nb_colis
                self.di_poin = self.quantity_done * self.product_id.weight 
                self.di_poib = self.di_poin + self.di_tare
                       
            elif self.di_un_saisie == "COLIS":
                self.di_nb_colis = self.di_qte_un_saisie
                self.quantity_done = self.di_product_packaging_id.qty * self.di_nb_colis
                self.di_nb_pieces = self.di_product_packaging_id.di_qte_cond_inf * self.di_nb_colis
                if self.di_type_palette_id.di_qte_cond_inf != 0.0:                
                    self.di_nb_palette = self.di_nb_colis / self.di_type_palette_id.di_qte_cond_inf
                else:
                    self.di_nb_palette = self.di_nb_colis
                self.di_poin = self.quantity_done * self.product_id.weight 
                self.di_poib = self.di_poin + self.di_tare
                                      
            elif self.di_un_saisie == "PALETTE":            
                self.di_nb_palette = self.di_qte_un_saisie
                if self.di_type_palette_id.di_qte_cond_inf != 0.0:
                    self.di_nb_colis = self.di_nb_palette / self.di_type_palette_id.di_qte_cond_inf
                else:
                    self.di_nb_colis = self.di_nb_palette
                self.di_nb_pieces = self.di_product_packaging_id.di_qte_cond_inf * self.di_nb_colis
                self.quantity_done = self.di_product_packaging_id.qty * self.di_nb_colis
                self.di_poin = self.quantity_done * self.product_id.weight 
                self.di_poib = self.di_poin + self.di_tare
                 
            elif self.di_un_saisie == "POIDS":
                self.di_poin = self.di_qte_un_saisie
                self.di_poib = self.di_poin + self.di_tare
                self.quantity_done = self.di_poin
                if self.di_product_packaging_id.qty != 0.0:
                    self.di_nb_colis = self.quantity_done / self.di_product_packaging_id.qty
                else:
                    self.di_nb_colis = self.quantity_done
                if self.di_type_palette_id.di_qte_cond_inf != 0.0:    
                    self.di_nb_palette = self.di_nb_colis / self.di_type_palette_id.di_qte_cond_inf
                else:  
                    self.di_nb_palette = self.di_nb_colis
                self.di_nb_pieces = self.di_product_packaging_id.di_qte_cond_inf * self.di_nb_colis
                 
            else:
                self.di_poin = self.di_qte_un_saisie
                self.di_poib = self.di_poin + self.di_tare
                self.quantity_done = self.di_poin
                if self.di_product_packaging_id.qty != 0.0:
                    self.di_nb_colis = self.quantity_done / self.di_product_packaging_id.qty
                else:
                    self.di_nb_colis = self.quantity_done
                if self.di_type_palette_id.di_qte_cond_inf != 0.0:    
                    self.di_nb_palette = self.di_nb_colis / self.di_type_palette_id.di_qte_cond_inf
                else:  
                    self.di_nb_palette = self.di_nb_colis
                self.di_nb_pieces = self.di_product_packaging_id.di_qte_cond_inf * self.di_nb_colis
               
    @api.model
    def create(self, vals):               
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
                    #on attribue par défaut les valeurs de la ligne de commande   
                    vals["di_tare"] = Disaleorderline.di_tare   
                    vals["di_un_saisie"] = Disaleorderline.di_un_saisie
                    vals["di_type_palette_id"] = Disaleorderline.di_type_palette_id.id
                    vals["di_product_packaging_id"] = Disaleorderline.di_product_packaging_id.id                                                         
                    vals["di_qte_un_saisie"] = Disaleorderline.di_qte_un_saisie - Disaleorderline.di_qte_un_saisie_liv
                    vals["di_tare"] = Disaleorderline.di_poib
                                                     
        res = super(StockMove, self).create(vals)                           
        return res
 
class StockMoveLine(models.Model):
    _inherit = "stock.move.line"
      
    di_qte_un_saisie = fields.Float(string='Quantité en unité de saisie', store=True)  
     
    @api.multi                     
    @api.onchange('di_qte_un_saisie')
    def _di_recalcule_quantites(self):
        if self.ensure_one():
            if self.move_id.di_un_saisie == "PIECE":            
                self.qty_done = self.product_id.di_get_type_piece().qty * self.di_qte_un_saisie                               
            elif self.move_id.di_un_saisie == "COLIS":            
                self.qty_done = self.move_id.di_product_packaging_id.qty * self.di_qte_un_saisie                                            
            elif self.move_id.di_un_saisie == "PALETTE":    
                nbColis = 0.0                    
                if self.move_id.di_type_palette_id.di_qte_cond_inf != 0.0:
                    nbColis = self.di_qte_un_saisie / self.move_id.di_type_palette_id.di_qte_cond_inf
                else:
                    nbColis = self.di_qte_un_saisie            
                self.qty_done = self.move_id.di_product_packaging_id.qty * nbColis                         
            elif self.move_id.di_un_saisie == "POIDS":            
                self.qty_done = self.di_qte_un_saisie                    
            else:
                self.qty_done = self.di_qte_un_saisie
                
    