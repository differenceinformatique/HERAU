
# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, float_compare, float_is_zero
from datetime import datetime, timedelta
from odoo.exceptions import UserError, ValidationError, Warning
from ...difodoo_fichiers_base.controllers import di_ctrl_print
import ctypes
from math import ceil
from odoo.addons import decimal_precision as dp
from ...difodoo_fichiers_base.models import di_param
from functools import partial
from odoo.tools.misc import formatLang


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"
    
    modifparprg = False
    di_flg_msg_stock = True
    
    di_qte_un_saisie= fields.Float(string='Quantité en unité de saisie',store=True)
    di_un_saisie    = fields.Selection([("PIECE", "Pièce"), ("COLIS", "Colis"),("PALETTE", "Palette"),("KG","Kg")], string="Unité de saisie",store=True)
    di_type_palette_id  = fields.Many2one('product.packaging', string='Palette') 
#     di_nb_pieces    = fields.Integer(string='Nb pièces' ,compute="_compute_qte_aff",store=True) # doublon avec _di_recalcule_quantites
#     di_nb_colis     = fields.Integer(string='Nb colis',compute="_compute_qte_aff",store=True) # doublon avec _di_recalcule_quantites
#     di_nb_palette   = fields.Float(string='Nb palettes',compute="_compute_qte_aff",store=True) # doublon avec _di_recalcule_quantites
    di_nb_pieces    = fields.Integer(string='Nb pièces')
    di_nb_colis     = fields.Integer(string='Nb colis')
    di_nb_palette   = fields.Float(string='Nb palettes')
    di_poin         = fields.Float(string='Poids net',store=True)
    di_poib         = fields.Float(string='Poids brut',store=True)
    di_tare         = fields.Float(string='Tare',store=True)#,compute="_compute_tare")    
    di_un_prix      = fields.Selection([("PIECE", "Pièce"), ("COLIS", "Colis"),("PALETTE", "Palette"),("KG","Kg")], string="Unité de prix",store=True)

    di_flg_modif_uom = fields.Boolean()
#     di_flg_msg_stock = fields.Boolean(string="flag", default=False, store=True)
    

    di_qte_un_saisie_liv = fields.Float(string='Quantité livrée en unité de saisie', compute='_compute_qty_delivered')
    di_un_saisie_liv     = fields.Selection([("PIECE", "Pièce"), ("COLIS", "Colis"),("PALETTE", "Palette"),("KG","Kg")], string="Unité de saisie livrée")
    di_type_palette_liv_id  = fields.Many2one('product.packaging', string='Palette livrée') 
    di_nb_pieces_liv     = fields.Integer(string='Nb pièces livrées', compute='_compute_qty_delivered')
    di_nb_colis_liv      = fields.Integer(string='Nb colis livrés', compute='_compute_qty_delivered')
    di_nb_palette_liv    = fields.Float(string='Nb palettes livrées', compute='_compute_qty_delivered')
    di_poin_liv          = fields.Float(string='Poids net livré', compute='_compute_qty_delivered')
    di_poib_liv          = fields.Float(string='Poids brut livré', compute='_compute_qty_delivered')
    di_tare_liv          = fields.Float(string='Tare livrée', compute='_compute_qty_delivered')
    di_product_packaging_liv_id=fields.Many2one('product.packaging', string='Colis livré')
    
    di_qte_un_saisie_fac = fields.Float(string='Quantité facturée en unité de saisie',compute='_get_invoice_qty')
    di_un_saisie_fac     = fields.Selection([("PIECE", "Pièce"), ("COLIS", "Colis"),("PALETTE", "Palette"),("KG","Kg")], string="Unité de saisie facturés")
    di_type_palette_fac_id  = fields.Many2one('product.packaging', string='Palette facturée') 
    di_nb_pieces_fac     = fields.Integer(string='Nb pièces facturées')
    di_nb_colis_fac      = fields.Integer(string='Nb colis facturés')
    di_nb_palette_fac    = fields.Float(string='Nb palettes facturées')
    di_poin_fac          = fields.Float(string='Poids net facturé')
    di_poib_fac          = fields.Float(string='Poids brut facturé')
    di_tare_fac          = fields.Float(string='Tare facturée')
    di_product_packaging_fac_id=fields.Many2one('product.packaging', string='Colis facturé')
    di_un_prix_fac      = fields.Selection([("PIECE", "Pièce"), ("COLIS", "Colis"),("PALETTE", "Palette"),("KG","Kg")], string="Unité de prix facturé",store=True)
    
    di_qte_a_facturer_un_saisie = fields.Float(string='Quantité à facturer en unité de saisie',compute='_get_to_invoice_qty')
    di_poin_a_facturer = fields.Float(string='Poids net à facturer',compute='_get_to_invoice_qty')
    di_poib_a_facturer = fields.Float(string='Poids brut à facturer',compute='_get_to_invoice_qty')
    di_nb_pieces_a_facturer = fields.Integer(string='Nb pièces à facturer',compute='_get_to_invoice_qty')
    di_nb_colis_a_facturer = fields.Integer(string='Nb colis à facturer',compute='_get_to_invoice_qty')
    di_nb_palette_a_facturer = fields.Float(string='Nb palette à facturer',compute='_get_to_invoice_qty')
    
    di_spe_saisissable = fields.Boolean(string='Champs spé saisissables',default=True,compute='_di_compute_spe_saisissable',store=True)          
    di_dern_prix = fields.Float(string='Dernier prix', digits=dp.get_precision('Product Price'),compute='_di_compute_dernier_prix',store=True)    
    di_marge_prc = fields.Float(string='% marge',compute='_di_calul_marge_prc',store=True)    
    di_marge_inf_seuil = fields.Boolean(string='Marge inférieure au seuil',default = False, compute='_di_compute_marge_seuil',store=True)    
    di_tare_un = fields.Float(string='Tare unitaire')  
    
    di_mode_saisie = fields.Char(string='Mode saisie',compute='_compte_mode_saisie')
    
    def _compte_mode_saisie(self):
        self.di_mode_saisie = 'bottom'        
   

    @api.multi 
    @api.onchange('di_poib')
    def _di_onchange_poib(self):
        if self.ensure_one():                    
            if self.di_un_saisie == 'KG':
                self.di_qte_un_saisie = self.di_poib
            else:
                self.di_poin = self.di_poib - self.di_tare
                if self.product_uom:
                    if self.product_uom.name.lower() == 'kg' and self.product_uom_qty != self.di_poin: # si la qté std n'est pas modifiée le flag modifparprg reste à vrai
                        SaleOrderLine.modifparprg=True
                        self.product_uom_qty = self.di_poin
                                
    @api.multi 
    @api.onchange('di_poin')
    def _di_onchange_poin(self):
        if self.ensure_one():
            self.di_tare = self.di_poib-self.di_poin      
#             self.di_poib = self.di_poin+self.di_tare       
#             if self.di_un_saisie == 'KG':
#                 self.di_qte_un_saisie = self.di_poib
#             else:       
            if self.di_un_saisie != 'KG':         
                if self.product_uom:
                    if self.product_uom.name.lower() == 'kg' and self.product_uom_qty != self.di_poin: # si la qté std n'est pas modifiée le flag modifparprg reste à vrai
                        SaleOrderLine.modifparprg=True
                        self.product_uom_qty = self.di_poin
    
    @api.multi 
    @api.onchange('di_tare')
    def _di_onchange_tare(self):
        if self.ensure_one():    
            self.di_poin = self.di_poib - self.di_tare        
            if self.di_un_saisie == 'KG':
                self.di_qte_un_saisie = self.di_poib
            else:
                if self.product_uom:
                    if self.product_uom.name.lower() == 'kg' and self.product_uom_qty != self.di_poin:# si la qté std n'est pas modifiée le flag modifparprg reste à vrai
                        SaleOrderLine.modifparprg=True
                        self.product_uom_qty = self.di_poin
                
                        
    @api.multi    
    @api.onchange('product_uom_qty')
    def _di_modif_qte_un_mesure(self):
        if self.ensure_one():
            if not self.product_id and self.product_uom_qty == 1:
                # par défaut la quantité est à 1, ce qui pose problème par la suite
                self.product_uom_qty = 0
            if self.product_id:
                if SaleOrderLine.modifparprg == False:
                    if self.product_uom:
                        if self.product_uom.name.lower() == 'kg':
                            # si géré au kg, on ne modife que les champs poids
                            self.di_poin = self.product_uom_qty
                            self.di_poib = self.di_poin + self.di_tare
                            
                        if self.product_uom.name == 'Unit(s)' or self.product_uom.name == 'Pièce' :
                            self.di_nb_pieces = ceil(self.product_uom_qty)
                        if self.product_uom.name.lower() ==  'colis' :
                            self.di_nb_colis = ceil(self.product_uom_qty)
                        if self.product_uom.name.lower() ==  'palette' :
                            self.di_nb_palette = ceil(self.product_uom_qty)
#                         else:
#                             # sinon on recalcule les autres unité à partir de la quantité en unité de mesure    
#                             if self.product_id.di_get_type_piece().qty != 0.0:
#                                 self.di_nb_pieces = ceil(self.product_uom_qty/self.product_id.di_get_type_piece().qty)
#                             else:
#                                 self.di_nb_pieces = ceil(self.product_uom_qty)                                
#                             if self.product_packaging.qty != 0.0 :
#                                 self.di_nb_colis = ceil(self.product_uom_qty / self.product_packaging.qty)
#                             else:      
#                                 self.di_nb_colis = ceil(self.product_uom_qty)             
#                             if self.di_type_palette_id.di_qte_cond_inf != 0.0:
#                                 self.di_nb_palette = self.di_nb_colis / self.di_type_palette_id.di_qte_cond_inf
#                             else:
#                                 self.di_nb_palette = self.di_nb_colis
# 
#                         self.di_poin = self.product_uom_qty * self.product_id.weight 
#                         self.di_poib = self.di_poin + self.di_tare
#                                 
# temporaire herau
#                         if self.di_un_saisie == "PIECE":
#                             self.di_qte_un_saisie = self.di_nb_pieces
#                         elif self.di_un_saisie == "COLIS":
#                             self.di_qte_un_saisie = self.di_nb_colis
#                         elif self.di_un_saisie == "PALETTE":
#                             self.di_qte_un_saisie = self.di_nb_palette 
#                         elif self.di_un_saisie == "KG":
#                             self.di_qte_un_saisie = self.di_poib
                            
                        self.di_flg_modif_uom = True
                SaleOrderLine.modifparprg=False
    
    @api.multi    
    @api.onchange('di_qte_un_saisie', 'di_un_saisie','di_type_palette_id','product_packaging')
    def _di_recalcule_quantites(self):
        if self.ensure_one():
            if self.product_id:
                #if self.di_qte_un_saisie!=0 or self.di_nb_pieces!=0 or self.di_nb_colis!=0 or self.di_nb_palette!=0 or self.di_poin!=0 or self.di_poib!=0:
                #    # on ne passe que si une des quantités est différente de 0, sinon on y passe en initialisation de l'unité de saisie/colisage
                product_uom_qty = self.product_uom_qty  # on fait une sauvegarde de la quantité en unité de mesure, on e bascule le flag que si elle change                         
                if self.di_flg_modif_uom == False:
                    self.di_tare_un = 0.0
                    self.di_tare = 0.0
                    #SaleOrderLine.modifparprg = True
                    if self.di_un_saisie == "PIECE":
                        self.di_nb_pieces = ceil(self.di_qte_un_saisie)
                        self.product_uom_qty = self.product_id.di_get_type_piece().qty * self.di_nb_pieces
                        if self.product_packaging.qty != 0.0 :
                            self.di_nb_colis = ceil(self.product_uom_qty / self.product_packaging.qty)
                        else:      
                            self.di_nb_colis = ceil(self.product_uom_qty)             
                        if self.di_type_palette_id.di_qte_cond_inf != 0.0:
                            self.di_nb_palette = self.di_nb_colis / self.di_type_palette_id.di_qte_cond_inf
                        else:
                            self.di_nb_palette = self.di_nb_colis
                        self.di_poin = self.product_uom_qty * self.product_id.weight 
                        self.di_poib = self.di_poin + self.di_tare
                              
                    elif self.di_un_saisie == "COLIS":
                        self.di_nb_colis = ceil(self.di_qte_un_saisie)
                        self.product_uom_qty = self.product_packaging.qty * self.di_nb_colis
                        self.di_nb_pieces = ceil(self.product_packaging.di_qte_cond_inf * self.di_nb_colis)
                        if self.di_type_palette_id.di_qte_cond_inf !=0.0:                
                            self.di_nb_palette = self.di_nb_colis / self.di_type_palette_id.di_qte_cond_inf
                        else:
                            self.di_nb_palette = self.di_nb_colis
                        self.di_poin = self.product_uom_qty * self.product_id.weight 
                        self.di_poib = self.di_poin + self.di_tare
                                             
                    elif self.di_un_saisie == "PALETTE":            
                        self.di_nb_palette = self.di_qte_un_saisie
                        if self.di_type_palette_id.di_qte_cond_inf!=0.0:
                            self.di_nb_colis = ceil(self.di_nb_palette * self.di_type_palette_id.di_qte_cond_inf)
                        else:
                            self.di_nb_colis = ceil(self.di_nb_palette)
                        self.di_nb_pieces = ceil(self.product_packaging.di_qte_cond_inf * self.di_nb_colis)
                        self.product_uom_qty = self.product_packaging.qty * self.di_nb_colis
                        self.di_poin = self.product_uom_qty * self.product_id.weight 
                        self.di_poib = self.di_poin + self.di_tare
                        
                    elif self.di_un_saisie == "KG":    
                        self.di_poib = self.di_qte_un_saisie
                        self.di_poin = self.di_poib - self.di_tare
    #                     self.product_uom_qty = self.di_poin
                        if self.product_id.weight  != 0.0:
                            self.di_nb_pieces = ceil(self.di_poin / self.product_id.weight )
                        else:
                            self.di_nb_pieces = ceil(self.di_poin)                                            
                        if self.product_packaging.qty !=0.0:
                            self.di_nb_colis = ceil(self.di_nb_pieces / self.product_packaging.qty)
                        else:
                            self.di_nb_colis = ceil(self.di_nb_pieces)                            
                        self.product_uom_qty = self.product_packaging.qty * self.di_nb_colis                            
                        if self.di_type_palette_id.di_qte_cond_inf !=0.0:    
                            self.di_nb_palette = self.di_nb_colis / self.di_type_palette_id.di_qte_cond_inf
                        else:  
                            self.di_nb_palette = self.di_nb_colis                        
                        
                    else:
                        self.di_poib = self.di_qte_un_saisie
                        self.di_poin = self.di_poib - self.di_tare
    #                     self.product_uom_qty = self.di_poin
                        if self.product_id.weight  != 0.0:
                            self.di_nb_pieces = ceil(self.di_poin / self.product_id.weight )
                        else:
                            self.di_nb_pieces = ceil(self.di_poin)                                            
                        if self.product_packaging.qty !=0.0:
                            self.di_nb_colis = ceil(self.di_nb_pieces / self.product_packaging.qty)
                        else:
                            self.di_nb_colis = ceil(self.di_nb_pieces)                           
                        self.product_uom_qty = self.product_packaging.qty * self.di_nb_colis                           
                        if self.di_type_palette_id.di_qte_cond_inf !=0.0:    
                            self.di_nb_palette = self.di_nb_colis / self.di_type_palette_id.di_qte_cond_inf
                        else:  
                            self.di_nb_palette = self.di_nb_colis
                            
                if product_uom_qty != self.product_uom_qty:
                    # la quantité en unité de mesure à changer, on met le flag pour ne pas recalculé les qtés spé
                    SaleOrderLine.modifparprg = True
                            
    @api.multi    
    @api.onchange('di_nb_colis', 'di_tare_un','di_qte_un_saisie')
    def _di_recalcule_tare(self):
        if self.ensure_one():
            self.di_tare = self.di_tare_un * self.di_nb_colis
               
#     @api.multi    ; doublon avec _di_recalcule_quantites
#     @api.depends('di_qte_un_saisie', 'di_un_saisie','di_type_palette_id','product_packaging')
#     def _compute_qte_aff(self):
#         #if self.ensure_one():
#         for sol in self:
#             if sol.di_flg_modif_uom == False:
#                 if sol.di_un_saisie == "PIECE":
#                     sol.di_nb_pieces = ceil(sol.di_qte_un_saisie)            
#                     if sol.product_packaging.qty != 0.0 :
#                         sol.di_nb_colis = ceil(sol.product_uom_qty / sol.product_packaging.qty)
#                     else:      
#                         sol.di_nb_colis = ceil(sol.product_uom_qty)             
#                     if sol.di_type_palette_id.di_qte_cond_inf != 0.0:
#                         sol.di_nb_palette = sol.di_nb_colis / sol.di_type_palette_id.di_qte_cond_inf
#                     else:
#                         sol.di_nb_palette = sol.di_nb_colis                               
#                             
#                 elif sol.di_un_saisie == "COLIS":
#                     sol.di_nb_colis = ceil(sol.di_qte_un_saisie)            
#                     sol.di_nb_pieces = ceil(sol.product_packaging.di_qte_cond_inf * sol.di_nb_colis)
#                     if sol.di_type_palette_id.di_qte_cond_inf !=0.0:                
#                         sol.di_nb_palette = sol.di_nb_colis / sol.di_type_palette_id.di_qte_cond_inf
#                     else:
#                         sol.di_nb_palette = sol.di_nb_colis                              
#                                            
#                 elif sol.di_un_saisie == "PALETTE":            
#                     sol.di_nb_palette = sol.di_qte_un_saisie
#                     if sol.di_type_palette_id.di_qte_cond_inf!=0.0:
#                         sol.di_nb_colis = ceil(sol.di_nb_palette * sol.di_type_palette_id.di_qte_cond_inf)
#                     else:
#                         sol.di_nb_colis = ceil(sol.di_nb_palette)
#                     sol.di_nb_pieces = ceil(sol.product_packaging.di_qte_cond_inf * sol.di_nb_colis)                                           
#                       
#                 elif sol.di_un_saisie == "KG":                                          
#                     if sol.product_packaging.qty !=0.0:
#                         sol.di_nb_colis = ceil(sol.product_uom_qty / sol.product_packaging.qty)
#                     else:
#                         sol.di_nb_colis = ceil(sol.product_uom_qty)
#                     if sol.di_type_palette_id.di_qte_cond_inf !=0.0:    
#                         sol.di_nb_palette = sol.di_nb_colis / sol.di_type_palette_id.di_qte_cond_inf
#                     else:  
#                         sol.di_nb_palette = sol.di_nb_colis
#                     sol.di_nb_pieces = ceil(sol.product_packaging.di_qte_cond_inf * sol.di_nb_colis)
#                       
#                 else:                                    
#                     if sol.product_packaging.qty !=0.0:
#                         sol.di_nb_colis = ceil(sol.product_uom_qty / sol.product_packaging.qty)
#                     else:
#                         sol.di_nb_colis = ceil(sol.product_uom_qty)
#                     if sol.di_type_palette_id.di_qte_cond_inf !=0.0:    
#                         sol.di_nb_palette = sol.di_nb_colis / sol.di_type_palette_id.di_qte_cond_inf
#                     else:  
#                         sol.di_nb_palette = sol.di_nb_colis
#                     sol.di_nb_pieces = ceil(sol.product_packaging.di_qte_cond_inf * sol.di_nb_colis)
#             else:           
#                 if sol.product_id.di_get_type_piece().qty != 0.0:
#                     sol.di_nb_pieces = ceil(sol.product_uom_qty/sol.product_id.di_get_type_piece().qty)
#                 else:
#                     sol.di_nb_pieces = ceil(sol.product_uom_qty)                                
#                 if sol.product_packaging.qty != 0.0 :
#                     sol.di_nb_colis = ceil(sol.product_uom_qty / sol.product_packaging.qty)
#                 else:      
#                     sol.di_nb_colis = ceil(sol.product_uom_qty)             
#                 if sol.di_type_palette_id.di_qte_cond_inf != 0.0:
#                     sol.di_nb_palette = sol.di_nb_colis / sol.di_type_palette_id.di_qte_cond_inf
#                 else:
#                     sol.di_nb_palette = sol.di_nb_colis
#                       
    
    @api.multi
    @api.depends('move_ids.state', 'move_ids.scrapped', 'move_ids.product_uom_qty', 'move_ids.product_uom', 'move_ids.di_qte_un_saisie'
                 , 'move_ids.di_nb_pieces', 'move_ids.di_nb_colis', 'move_ids.di_nb_palette', 'move_ids.di_poin', 'move_ids.di_poib')
    def _compute_qty_delivered(self):
        super(SaleOrderLine, self)._compute_qty_delivered()
        for line in self:  # TODO: maybe one day, this should be done in SQL for performance sake
            if line.qty_delivered_method == 'stock_move':
                qte_un_saisie = 0.0
                pieces = 0.0
                colis = 0.0
                palettes = 0.0
                poib = 0.0
                poin = 0.0         
                tare = 0.0      
                for move in line.move_ids.filtered(lambda r: r.state == 'done' and not r.scrapped and line.product_id == r.product_id):
                    if move.location_dest_id.usage == "customer":
                        if not move.origin_returned_move_id or (move.origin_returned_move_id and move.to_refund):
                            qte_un_saisie += move.di_qte_un_saisie
                            pieces += move.di_nb_pieces
                            colis += move.di_nb_colis
                            palettes += move.di_nb_palette
                            poib += move.di_poib
                            poin += move.di_poin
                            tare += move.di_tare
                   
                    elif move.location_dest_id.usage != "customer" and move.to_refund:
                        qte_un_saisie -= move.di_qte_un_saisie
                        pieces -= move.di_nb_pieces
                        colis -= move.di_nb_colis
                        palettes -= move.di_nb_palette
                        poib -= move.di_poib
                        poin -= move.di_poin
                        tare -= move.di_tare
                        
                        
                    line.di_type_palette_liv_id  = move.di_type_palette_id
                    line.di_un_saisie_liv     = move.di_un_saisie
                    line.di_product_packaging_liv_id = move.di_product_packaging_id
                     
                line.di_tare_liv          = tare
                line.di_qte_un_saisie_liv = qte_un_saisie
                line.di_nb_pieces_liv = pieces
                line.di_nb_colis_liv = colis
                line.di_nb_palette_liv = palettes
                line.di_poib_liv = poib
                line.di_poin_liv = poin
                
                # c'est la quantité standard qui fait foi, on remplace la qté spé correspondant à l'unité de mesure
                if line.product_uom:
                    if line.product_uom.name.lower() == 'kg':
                        line.di_poin_liv = line.qty_delivered
                        line.di_poib_liv = line.di_poin_liv + line.di_tare_liv
                    else:
                        if line.product_id.di_get_type_piece().qty == 1.0:  # si pas au kg, et coef 1, équivalent à l'unité de mesure, maj
                            line.di_nb_pieces_liv = line.qty_delivered
                        if line.product_packaging.qty == 1.0:   # si pas au kg, et coef 1, équivalent à l'unité de mesure, maj
                            line.di_nb_colis_liv = line.qty_delivered
                        if line.di_type_palette_id.di_qte_cond_inf * line.product_packaging.qty == 1.0:   # si pas au kg, et coef 1, équivalent à l'unité de mesure, maj
                            line.di_nb_palette_liv = line.qty_delivered
                
    @api.multi
    @api.depends('di_marge_prc','company_id.di_param_id.di_seuil_marge_prc')#,'di_param_id.di_seuil_marge_prc')
    def _di_compute_marge_seuil(self):   
        for sol in self:
            if sol.di_marge_prc < sol.company_id.di_param_id.di_seuil_marge_prc:     
                sol.di_marge_inf_seuil = True
            else:
                sol.di_marge_inf_seuil = False
            
    
    @api.multi
    @api.depends('price_subtotal','product_uom_qty','purchase_price')
    def _di_calul_marge_prc(self):
        for sol in self:
            if sol.product_uom_qty and sol.product_uom_qty != 0.0:
                qte = sol.product_uom_qty
            else:
                qte = 1.0
            if sol.purchase_price and sol.purchase_price !=0.0:
                sol.di_marge_prc = (sol.price_subtotal/qte - sol.purchase_price )*100/sol.purchase_price            
            else:
                sol.di_marge_prc = sol.price_subtotal/qte*100
        
        
    def _get_dernier_prix(self):
        prix = 0.0
        l = self.search(['&', ('product_id', '=', self.product_id.id), ('order_partner_id', '=', self.order_partner_id.id),('order_id.date_order','<',self.order_id.date_order)], limit=1).sorted(key=lambda t: t.order_id.date_order,reverse=True)
        if l.price_unit:
            prix = l.price_unit            
        return prix
                      
    @api.multi
    @api.depends('product_id','order_partner_id','order_id.date_order')
    def _di_compute_dernier_prix(self):        
        for sol in self:
            sol.di_dern_prix =sol._get_dernier_prix()    
              
    def di_recherche_prix_unitaire(self,prixOrig, tiers, article, di_un_prix , qte, date,typecol,typepal):
        if not prixOrig or prixOrig ==0.0:    
            prixFinal = 0.0       
            prixFinal =self.env["di.tarifs"]._di_get_prix(tiers,article,di_un_prix,qte,date,typecol,typepal)
            if prixFinal == 0.0:
                prixFinal = prixOrig
    #             if prixOrig == 0.0:
    #                 raise ValidationError("Le prix unitaire de la ligne est à 0 !")
        else:
            prixFinal = prixOrig
        return prixFinal  
                       
    @api.multi
    @api.depends('product_id.di_spe_saisissable','product_id','di_qte_un_saisie')
    def _di_compute_spe_saisissable(self):     
        for sol in self:   
            sol.di_spe_saisissable =sol.product_id.di_spe_saisissable     

    @api.depends('product_uom_qty', 'discount', 'price_unit', 'tax_id','di_qte_un_saisie','di_nb_pieces','di_nb_colis','di_nb_palette','di_poin','di_poib','di_tare','di_un_prix')
    def _compute_amount(self):
        # copie standard
        """
        Compute the amounts of the SO line.
        """
        for line in self:
            price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
            # modif de la quantité à prendre en compte
            di_qte_prix = 0.0
            if line.di_un_prix == "PIECE":
                di_qte_prix = line.di_nb_pieces
            elif line.di_un_prix == "COLIS":
                di_qte_prix = line.di_nb_colis
            elif line.di_un_prix == "PALETTE":
                di_qte_prix = line.di_nb_palette
            elif line.di_un_prix == "KG":
                di_qte_prix = line.di_poin
            elif line.di_un_prix == False or line.di_un_prix == '':
                di_qte_prix = line.product_uom_qty
             
            taxes = line.tax_id.compute_all(price, line.order_id.currency_id, di_qte_prix, product=line.product_id, partner=line.order_id.partner_shipping_id)
            line.update({
                'price_tax': sum(t.get('amount', 0.0) for t in taxes.get('taxes', [])),
                'price_total': taxes['total_included'],
                'price_subtotal': taxes['total_excluded'],
            })
       
    @api.multi
    def _get_qte_un_saisie_liv(self):
        self.ensure_one()        
        qty = 0.0
        for move in self.move_ids.filtered(lambda r: r.state == 'done' and not r.scrapped):
            if move.location_dest_id.usage == "customer":
                if not move.origin_returned_move_id:
                    qty+=move.di_qte_un_saisie                    
            elif move.location_dest_id.usage != "customer" and move.to_refund:
                qty-=move.di_qte_un_saisie                
        return qty
   
    @api.multi
    def _get_nb_pieces_liv(self):
        self.ensure_one()        
        qty = 0.0
        for move in self.move_ids.filtered(lambda r: r.state == 'done' and not r.scrapped):
            if move.location_dest_id.usage == "customer":
                if not move.origin_returned_move_id:
                    qty+=move.di_nb_pieces                    
            elif move.location_dest_id.usage != "customer" and move.to_refund:
                qty-=move.di_nb_pieces                
        return qty
    
    @api.multi
    def _get_nb_colis_liv(self):
        self.ensure_one()        
        qty = 0.0
        for move in self.move_ids.filtered(lambda r: r.state == 'done' and not r.scrapped):
            if move.location_dest_id.usage == "customer":
                if not move.origin_returned_move_id:
                    qty+=move.di_nb_colis                    
            elif move.location_dest_id.usage != "customer" and move.to_refund:
                qty-=move.di_nb_colis                
        return qty
    
    @api.multi
    def _get_nb_palettes_liv(self):
        self.ensure_one()        
        qty = 0.0
        for move in self.move_ids.filtered(lambda r: r.state == 'done' and not r.scrapped):
            if move.location_dest_id.usage == "customer":
                if not move.origin_returned_move_id:
                    qty+=move.di_nb_palette                    
            elif move.location_dest_id.usage != "customer" and move.to_refund:
                qty-=move.di_nb_palette                
        return qty
    
    @api.multi
    def _get_poin_liv(self):
        self.ensure_one()        
        qty = 0.0
        for move in self.move_ids.filtered(lambda r: r.state == 'done' and not r.scrapped):
            if move.location_dest_id.usage == "customer":
                if not move.origin_returned_move_id:
                    qty+=move.di_poin                    
            elif move.location_dest_id.usage != "customer" and move.to_refund:
                qty-=move.di_poin                
        return qty
    
    @api.multi
    def _get_poib_liv(self):
        self.ensure_one()        
        qty = 0.0
        for move in self.move_ids.filtered(lambda r: r.state == 'done' and not r.scrapped):
            if move.location_dest_id.usage == "customer":
                if not move.origin_returned_move_id:
                    qty+=move.di_poib                    
            elif move.location_dest_id.usage != "customer" and move.to_refund:
                qty-=move.di_poib                
        return qty
    
               
    @api.multi
    @api.onchange('product_id')
    def _di_charger_valeur_par_defaut(self):
        if self.ensure_one():
            SaleOrderLine.di_flg_msg_stock = False
            if self.order_partner_id and self.product_id:
                ref = self.env['di.ref.art.tiers'].search([('di_partner_id','=',self.order_partner_id.id),('di_product_id','=',self.product_id.id)],limit=1)
            else:
                ref = False
            if ref:
                self.di_un_saisie = ref.di_un_saisie
                self.di_type_palette_id = ref.di_type_palette_id
                self.product_packaging = ref.di_type_colis_id    
                self.di_un_prix = ref.di_un_prix    
                self.di_spe_saisissable = self.product_id.di_spe_saisissable  
             
            else:
                if self.product_id:
                    self.di_un_saisie = self.product_id.di_un_saisie
                    self.di_type_palette_id = self.product_id.di_type_palette_id
                    self.product_packaging = self.product_id.di_type_colis_id    
                    self.di_un_prix = self.product_id.di_un_prix    
                    self.di_spe_saisissable = self.product_id.di_spe_saisissable                
                   
                
    @api.multi
    @api.onchange('product_id')
    def product_id_change(self):
        result=super(SaleOrderLine, self).product_id_change()
        #surcharge de la procédure pour recalculer le prix car elle est appelée après _di_changer_prix quand on modifie l'article
        vals = {}
        if self.product_id and self.di_un_prix:
#             if vals.get("price_unit"):
            # modif de la quantité à prendre en compte
            di_qte_prix = 0.0
            if self.di_un_prix == "PIECE":
                di_qte_prix = self.di_nb_pieces
            elif self.di_un_prix == "COLIS":
                di_qte_prix = self.di_nb_colis
            elif self.di_un_prix == "PALETTE":
                di_qte_prix = self.di_nb_palette
            elif self.di_un_prix == "KG":
                di_qte_prix = self.di_poin
            elif self.di_un_prix == False or self.di_un_prix == '':
                di_qte_prix = self.product_uom_qty
                
            vals['price_unit'] = self.di_recherche_prix_unitaire(self.price_unit,self.order_id.partner_id,self.product_id,self.di_un_prix,di_qte_prix,self.order_id.date_order,self.product_packaging,self.di_type_palette_id)
            self.update(vals)       
        return result
    
    @api.onchange('product_uom', 'product_uom_qty')
    def product_uom_change(self):
        if not self.price_unit or self.price_unit==0.0:
            super(SaleOrderLine, self).product_uom_change()
        #surcharge de la procédure pour recalculer le prix car elle est appelée après _di_changer_prix quand on modifie l'article
        if self.product_id and self.di_un_prix:            
            di_qte_prix = 0.0
            if self.di_un_prix == "PIECE":
                di_qte_prix = self.di_nb_pieces
            elif self.di_un_prix == "COLIS":
                di_qte_prix = self.di_nb_colis
            elif self.di_un_prix == "PALETTE":
                di_qte_prix = self.di_nb_palette
            elif self.di_un_prix == "KG":
                di_qte_prix = self.di_poin
            elif self.di_un_prix == False or self.di_un_prix == '':
                di_qte_prix = self.product_uom_qty
            self.price_unit = self.di_recherche_prix_unitaire(self.price_unit,self.order_id.partner_id,self.product_id,self.di_un_prix,di_qte_prix,self.order_id.date_order,self.product_packaging,self.di_type_palette_id)       
                
    @api.multi
    @api.onchange('product_id','order_id.partner_id','order_id.date_order','di_un_prix','di_qte_un_saisie','di_nb_pieces','di_nb_colis','di_nb_palette','di_poin','di_poib','di_tare','product_uom_qty')
    def _di_changer_prix(self):
        for line in self:
            di_qte_prix = 0.0
            if line.di_un_prix == "PIECE":
                di_qte_prix = line.di_nb_pieces
            elif line.di_un_prix == "COLIS":
                di_qte_prix = line.di_nb_colis
            elif line.di_un_prix == "PALETTE":
                di_qte_prix = line.di_nb_palette
            elif line.di_un_prix == "KG":
                di_qte_prix = line.di_poin
            elif line.di_un_prix == False or line.di_un_prix == '':
                di_qte_prix = line.product_uom_qty             
            if line.product_id.id != False and line.di_un_prix:       
                line.price_unit = self.di_recherche_prix_unitaire(line.price_unit,line.order_id.partner_id,line.product_id,line.di_un_prix,di_qte_prix,line.order_id.date_order,line.product_packaging,line.di_type_palette_id)      
    @api.multi
    def _check_package(self):    
        # copie standard
        #surcharge pour enlever le contrôle sur le nombre d'unités saisies en fonction du colis choisi    
        return {}
        
    @api.onchange('product_uom_qty', 'product_uom', 'route_id')
    def _onchange_product_id_check_availability(self):
        # copie standard
        #surcharge pour enlever la remise à 0 de product_packaging
        
        if self.product_id.type == 'product':
            precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
            product = self.product_id.with_context(warehouse=self.order_id.warehouse_id.id,lang=self.order_id.partner_id.lang or self.env.user.lang or 'en_US')
            product_qty = self.product_uom._compute_quantity(self.product_uom_qty, self.product_id.uom_id)
            if float_compare(product.virtual_available, product_qty, precision_digits=precision) == -1:
                is_available = self._check_routing()
                if not is_available:
                    if not SaleOrderLine.di_flg_msg_stock:
                        SaleOrderLine.di_flg_msg_stock = True
#                         vals = {}
#                         vals['product_uom_qty'] = 999.0
#                         self.update(vals) 
                        message =  _('You plan to sell %s %s of %s but you only have %s %s available in %s warehouse.') % \
                                (self.product_uom_qty, self.product_uom.name, self.product_id.name, product.virtual_available, product.uom_id.name, self.order_id.warehouse_id.name)
                        # We check if some products are available in other warehouses.
                        if float_compare(product.virtual_available, self.product_id.virtual_available, precision_digits=precision) == -1:
                            message += _('\nThere are %s %s available across all warehouses.\n\n') % \
                                    (self.product_id.virtual_available, product.uom_id.name)
                            for warehouse in self.env['stock.warehouse'].search([]):
                                quantity = self.product_id.with_context(warehouse=warehouse.id).virtual_available
                                if quantity > 0:
                                    message += "%s: %s %s\n" % (warehouse.name, quantity, self.product_id.uom_id.name)
                        warning_mess = {
                            'title': _('Not enough inventory!'),
                            'message' : message
                        }
                        return {'warning': warning_mess}
        return {}
    
    @api.depends('di_qte_un_saisie_fac', 'di_qte_un_saisie_liv', 'di_qte_un_saisie', 'order_id.state',"di_poin_liv","di_poin_fac","di_poib_liv","di_poib_fac",  \
                 "di_nb_pieces","di_nb_pieces_liv","di_nb_pieces_fac","di_nb_colis","di_nb_colis_liv","di_nb_colis_fac","di_nb_palette","di_nb_palette_liv","di_nb_palette_fac")
    def _get_to_invoice_qty(self):
        
        """
        Compute the quantity to invoice. If the invoice policy is order, the quantity to invoice is
        calculated from the ordered quantity. Otherwise, the quantity delivered is used.
        """
        for line in self:
            if line.order_id.state in ['sale', 'done']:
                if line.product_id.invoice_policy == 'order':
                    line.di_qte_a_facturer_un_saisie = line.di_qte_un_saisie - line.di_qte_un_saisie_fac
                    line.di_poin_a_facturer = line.di_poin - line.di_poin_fac
                    line.di_poib_a_facturer = line.di_poib - line.di_poib_fac
                    line.di_nb_pieces_a_facturer = line.di_nb_pieces - line.di_nb_pieces_fac
                    line.di_nb_colis_a_facturer = line.di_nb_colis - line.di_nb_colis_fac
                    line.di_nb_palette_a_facturer = line.di_nb_palette - line.di_nb_palette_fac
                else:
                    line.di_qte_a_facturer_un_saisie = line.di_qte_un_saisie_liv - line.di_qte_un_saisie_fac
                    line.di_poin_a_facturer = line.di_poin_liv - line.di_poin_fac
                    line.di_poib_a_facturer = line.di_poib_liv - line.di_poib_fac
                    line.di_nb_pieces_a_facturer = line.di_nb_pieces_liv - line.di_nb_pieces_fac
                    line.di_nb_colis_a_facturer = line.di_nb_colis_liv - line.di_nb_colis_fac
                    line.di_nb_palette_a_facturer = line.di_nb_palette_liv - line.di_nb_palette_fac
            else:
                line.di_qte_a_facturer_un_saisie = 0.0
                line.di_poin_a_facturer = 0.0
                line.di_poib_a_facturer = 0.0
                line.di_nb_pieces_a_facturer = 0
                line.di_nb_colis_a_facturer = 0
                line.di_nb_palette_a_facturer = 0.0 
        super(SaleOrderLine, self)._get_to_invoice_qty()
                
    @api.depends('invoice_lines.invoice_id.state', 'invoice_lines.di_qte_un_saisie')
    def _get_invoice_qty(self):
        
        """
        Compute the quantity invoiced. If case of a refund, the quantity invoiced is decreased. Note
        that this is the case only if the refund is generated from the SO and that is intentional: if
        a refund made would automatically decrease the invoiced quantity, then there is a risk of reinvoicing
        it automatically, which may not be wanted at all. That's why the refund has to be created from the SO
        """
        for line in self:
            qty_invoiced = 0.0
            poin_invoiced = 0.0
            poib_invoiced = 0.0
            nbpieces_invoiced = 0.0
            nbcolis_invoiced = 0.0
            nbpal_invoiced = 0.0
            for invoice_line in line.invoice_lines:
                if invoice_line.invoice_id.state != 'cancel':
                    if invoice_line.invoice_id.type == 'out_invoice':
                        qty_invoiced += invoice_line.di_qte_un_saisie
                        poin_invoiced += invoice_line.di_poin
                        poib_invoiced += invoice_line.di_poib
                        nbpieces_invoiced += invoice_line.di_nb_pieces
                        nbcolis_invoiced += invoice_line.di_nb_colis
                        nbpal_invoiced += invoice_line.di_nb_palette
                    elif invoice_line.invoice_id.type == 'out_refund':
                        qty_invoiced -= invoice_line.di_qte_un_saisie
                        poin_invoiced -= invoice_line.di_poin
                        poib_invoiced -= invoice_line.di_poib
                        nbpieces_invoiced -= invoice_line.di_nb_pieces
                        nbcolis_invoiced -= invoice_line.di_nb_colis
                        nbpal_invoiced -= invoice_line.di_nb_palette
            line.di_qte_un_saisie_fac = qty_invoiced
            line.di_poin_fac = poin_invoiced
            line.di_poib_fac = poib_invoiced
            line.di_nb_pieces_fac = nbpieces_invoiced
            line.di_nb_colis_fac = nbcolis_invoiced
            line.di_nb_palette_fac = nbpal_invoiced
        super(SaleOrderLine, self)._get_invoice_qty()
        
     
        
    @api.multi
    def unlink(self):
        for line in self:
            if line.order_id.carrier_id:
                line.order_id.get_delivery_price() # on recalcul le prix du transport si on supprime une ligne
        res = super(SaleOrderLine, self).unlink()
        return res
        

class SaleOrder(models.Model):
    _inherit = "sale.order"
    di_period_fact = fields.Selection(string="Périodicité de Facturation", related='partner_id.di_period_fact')#,store=True)
    di_regr_fact = fields.Boolean(string="Regroupement sur Facture", related='partner_id.di_regr_fact')#,store=True)
    di_ref = fields.Char(string='Code Tiers', related='partner_id.ref')#,store=True)
    di_livdt = fields.Date(string='Date de livraison', copy=False, help="Date de livraison souhaitée",
                           default=lambda self : datetime.today().date()+timedelta(days=self.env['di.param'].search([('di_company_id','=',self.env.user.company_id.id)]).di_del_liv))
    di_prepdt = fields.Date(string='Date de préparation', copy=False, help="Date de préparation",
                           default=lambda wdate : datetime.today().date())    
    di_tournee = fields.Char(string='Tournée',help="Pour regroupement sur les bordereaux de transport")
    di_rangtournee = fields.Char(string='Rang dans la tournée',help="Pour ordre de tri sur les bordereaux de transport")
    di_nbpal = fields.Float(compute='_compute_di_nbpal_nbcol', store=True, digits=dp.get_precision('Product Unit of Measure'))
    di_nbcol = fields.Integer(compute='_compute_di_nbpal_nbcol', store=True)   
    di_nbex = fields.Integer("Nombre exemplaires",help="""Nombre d'exemplaires d'une impression.""",default=0)
    
    di_nb_lig = fields.Integer(string='Nb lignes saisies', compute="_compute_nb_lignes")
    

    @api.multi
    @api.depends("order_line")
    def _compute_nb_lignes(self):
        for order in self:
            order.di_nb_lig = len(order.order_line)
#     
#     di_taxe_ids = fields.One2many('di.sale.taxe', 'order_id', string='Taxes',compute="_amount_by_group")
#      
#     def prepare_taxe_lines(self,order):
#         ids = [] 
#         for ligne in order.amount_by_group:               
#             taxe_line = self.env['di.sale.taxe'].create({
#                 'name': ligne[0],
#                 'order_id': order.id,
#                 'amount': ligne[1],
#                 'base': ligne[2],
#                 })
#             ids.append(taxe_line.id)                        
#         return ids
#      
# 
#     def _compute_taxes(self):       
#         for order in self:
#             order.di_taxe_ids= [(6,0,self.prepare_taxe_lines(order))]                        
# #             order.update({                
# #                 'di_taxe_ids': [(6,0,self.prepare_taxe_lines(order))],                
# #             })

    @api.onchange("order_line")
    def di_recalcul_port(self):
        for order in self:
            if order.carrier_id:
                order.get_delivery_price()
#             if order.carrier_id and order.state in ("draft","sent") and order.delivery_rating_success:                
#             order.set_delivery_line() # Ne fonctionne pas -> message d'erreur unknown company_id # Pas possible ici car on est en création/modif de ligne -> conflit pour créer une autre ligne
                
                
    
    @api.multi
    @api.onchange("partner_id")
    def di_onchange_partner(self):
        for order in self:
            if order.partner_id:
                order.di_nbex = order.partner_id.di_nbex_cde
#     di_liste_taxes = fields.Char(compute='_di_compute_taxes',string='Détail des taxes')  
    
#     @api.onchange('order_line')
#     def di_onchange_order_line(self):
#         ligzero = False
#         for ol in self.order_line:
#             if ol.price_total==0.0:
#                 ligzero = True
#         if ligzero:        
#             return {'warning': {'Il exixste une ligne avec montant à 0.': _('Error'), 'message': _('Il exixste une ligne avec montant à 0 !'),},}
    
    @api.multi
    def action_print_invoice(self):
        invoices = self.mapped('invoice_ids')
        for invoice in invoices:
            invoice.invoice_print()
        
    
    @api.multi
    def imprimer_etiquettes(self):         
        param = self.env['di.param'].search([('di_company_id','=',self.env.user.company_id.id)])
        if param.di_label_id and param.di_label_id.file is not None and param.di_label_id.file != "":
            if param.di_printer_id : #and param.di_printer_id.adressip is not None and param.di_printer_id.adressip != "":
                if param.di_printer_id.realname is not None and param.di_printer_id.realname != "":
                    printer = param.di_printer_id.realname
                    label = param.di_label_id.file
                    data=''
                    for so in self:
                        for sol in so.order_line:
                            if sol.product_id.barcode : 
                                barcode = sol.product_id.barcode
                            else:
                                barcode="0000000000000"
                            if sol.move_ids:
                                for sm in sol.move_ids: 
                                    if sm.move_line_ids:
                                        for sml in sm.move_line_ids:
                                            qteform = "000000"
                                            qteform =str(int(sml.qty_done*100)) 
                                            qteform=qteform.rjust(6,'0')            
                                            if sml.lot_id:
                                                informations=[
                                                    ("codeart",sol.product_id.default_code),
                                                    ("des",sol.product_id.product_tmpl_id.name),
                                                    ("qte",sml.qty_done),                                       
                                                    ("codebarre",">802"+barcode+">83102"+qteform+">810"+">6"+sml.lot_id.name),
                                                    ("txtcb","(02)"+barcode+"(3102)"+qteform+"(10)"+sml.lot_id.name),
                                                    ("lot",sml.lot_id.name)
                                                    ]
                                            else:
                                                informations=[
                                                    ("codeart",sol.product_id.default_code),
                                                    ("des",sol.product_id.product_tmpl_id.name),
                                                    ("qte",sml.qty_done),                                        
                                                    ("codebarre",">802"+barcode+">83102"+qteform),
                                                    ("txtcb","(02)"+barcode+"(3102)"+qteform),
                                                    ("lot"," ")                                                                                                                                   
                                                    ]                                                
                                            data =data+ di_ctrl_print.format_data(label, '[', informations)    
#                                             di_ctrl_print.printlabelonwindows(printer,label,'[',informations)
                                    else:
                                        qteform = "000000"
                                        qteform =str(int(sm.product_qty*100)) 
                                        qteform=qteform.rjust(6,'0')
                                        informations=[
                                                    ("codeart",sol.product_id.default_code),
                                                    ("des",sol.product_id.product_tmpl_id.name),
                                                    ("qte",sm.product_qty),                                                                                
                                                    ("codebarre",">802"+barcode+">83102"+qteform),
                                                    ("txtcb","(02)"+barcode+"(3102)"+qteform),
                                                    ("lot"," ")                                                                                                                                                      
                                                    ]   
                                        data =data+ di_ctrl_print.format_data(label, '[', informations)                                             
#                                         di_ctrl_print.printlabelonwindows(printer,label,'[',informations)                                            
                            else:
                                qteform = "000000"
                                qteform =str(int(sol.product_uom_qty*100))
                                qteform=qteform.rjust(6,'0')
                                informations=[
                                    ("codeart",sol.product_id.default_code),
                                    ("des",sol.product_id.product_tmpl_id.name),
                                    ("qte",sol.product_uom_qty),
                                    #("codebarre",sol.product_id.barcode),                                            
                                    ("codebarre",">802"+barcode+">83102"+qteform),
                                    ("txtcb","(02)"+barcode+"(3102)"+qteform),
                                    ("lot"," ")                                                                                                                          
                                    ]
                                data =data+ di_ctrl_print.format_data(label, '[', informations)
#                                 di_ctrl_print.printlabelonwindows(printer,label,'[',informations)
                    di_ctrl_print.printlabelonwindows(printer,data)
                    
#     @api.depends('order_line')                
#     def _di_compute_taxes(self):
#         taxes = self._get_tax_amount_by_group()
#         self.di_liste_taxes = taxes
        
    
    def _amount_by_group(self):
        # copie standard
        for order in self:
            currency = order.currency_id or order.company_id.currency_id
            fmt = partial(formatLang, self.with_context(lang=order.partner_id.lang).env, currency_obj=currency)
            res = {}
            for line in order.order_line:
                # modif de la quantité à prendre en compte
                di_qte_prix = 0.0
                if line.di_un_prix == "PIECE":
                    di_qte_prix = line.di_nb_pieces
                elif line.di_un_prix == "COLIS":
                    di_qte_prix = line.di_nb_colis
                elif line.di_un_prix == "PALETTE":
                    di_qte_prix = line.di_nb_palette
                elif line.di_un_prix == "KG":
                    di_qte_prix = line.di_poin
                elif line.di_un_prix == False or line.di_un_prix == '':
                    di_qte_prix = line.product_uom_qty
                    
                price_reduce = line.price_unit * (1.0 - line.discount / 100.0)
                # Lecture de toutes  les taxes  de la ligne, y compris les taxes spé
                taxes = line.tax_id.compute_all(price_reduce, quantity=di_qte_prix, product=line.product_id, partner=order.partner_shipping_id)['taxes']
#   J'enlève un morceau du standard pour le remplacer afin de pouvoir afficher les taxes spé sur les impressions de commande
#                 for tax in line.tax_id:
#                     group = tax.tax_group_id
#                     res.setdefault(group, {'amount': 0.0, 'base': 0.0})
#                     for t in taxes:
#                         if t['id'] == tax.id or t['id'] in tax.children_tax_ids.ids:
#                             res[group]['amount'] += t['amount']
#                             res[group]['base'] += t['base']
#             res = sorted(res.items(), key=lambda l: l[0].sequence)
#             order.amount_by_group = [(
#                 l[0].name, l[1]['amount'], l[1]['base'],
#                 fmt(l[1]['amount']), fmt(l[1]['base']),
#                 len(res),
#             ) for l in res]

                for tax in taxes: # parcous des taxes trouvées
                    di_taxe = self.env['account.tax'].browse(tax['id'])# recherche de l'enreg de la taxe
                    group = di_taxe.tax_group_id
                    res.setdefault(group, {'amount': 0.0, 'base': 0.0})
                    #ajout des montants par groupe
                    res[group]['amount'] += tax['amount']
                    res[group]['base'] += tax['base']
                    if di_taxe.include_base_amount:
                        base_tax += di_taxe.compute_all(price_reduce + base_tax, quantity=1, product=line.product_id,partner=self.partner_shipping_id)['taxes'][0]['amount']                                            
            res = sorted(res.items(), key=lambda l: l[0].sequence)
            order.amount_by_group = [(
                l[0].name, l[1]['amount'], l[1]['base'],
                fmt(l[1]['amount']), fmt(l[1]['base']),
                len(res),
            ) for l in res]
#             order.di_taxe_ids =[(6,0,self.prepare_taxe_lines(order))]           
    
    @api.multi
    @api.onchange('di_livdt')
    def modif_livdt(self):
        if self.di_livdt<datetime.today().date():
            return {'warning': {'Erreur date livraison': _('Error'), 'message': _('La date de livraison ne peut être inférieure à la date du jour !'),},}       
        self.di_prepdt = self.di_livdt + timedelta(days=-self.env['di.param'].search([('di_company_id','=',self.env.user.company_id.id)]).di_del_liv)
        if self.di_prepdt<datetime.today().date():
            self.di_prepdt=datetime.today().date()
        self.requested_date = self.di_livdt
     
    @api.multi
    @api.onchange('di_prepdt')
    def modif_prepdt(self):
        if self.di_prepdt<datetime.today().date():
            return {'warning': {'Erreur date préparation': _('Error'), 'message': _('La date de préparation ne peut être inférieure à la date du jour !'),},}
        self.di_livdt = self.di_prepdt + timedelta(days=self.env['di.param'].search([('di_company_id','=',self.env.user.company_id.id)]).di_del_liv)
        self.requested_date = self.di_livdt
     
    def _force_lines_to_invoice_policy_order(self):
        super(SaleOrder, self)._force_lines_to_invoice_policy_order()
        for line in self.order_line:
            if self.state in ['sale', 'done']:
                line.di_qte_a_facturer_un_saisie = line.di_qte_un_saisie - line.di_qte_un_saisie_fac
            else:
                line.di_qte_a_facturer_un_saisie = 0   
                
#         <button name="333" string="Créer une facture" type="action" class="btn-primary" attrs="{'invisible': [('invoice_status', '!=', 'to invoice')]}" modifiers="{'invisible':[['invoice_status','!=','to invoice']]}" options="{}"/>
                
                
    @api.multi
    def di_action_facturer(self):
        for order in self:
            if order.state in ('draft','sent'):
                order.action_confirm()
                livraisons = order.mapped('picking_ids')
                for livraison in livraisons:
                    livraison.action_assign()
                    if livraison.state=='assigned':
                        livraison.button_validate()
                        order.action_invoice_create(grouped=False)
                        invoice = order.mapped('invoice_ids')
                        param = self.env['di.param'].search([('di_company_id','=',self.env.user.company_id.id)])
                        
                        if param.di_autovalid_fact_ven:
                            invoice.action_invoice_open()
        
        return self.action_view_invoice() 
    
    @api.multi
    def di_action_livrer(self):
        for order in self:
            if order.state in ('draft','sent'):
                order.action_confirm()
                livraisons = order.mapped('picking_ids')
                for livraison in livraisons:
                    livraison.action_assign()
                    if livraison.state=='assigned':
                        livraison.button_validate()                                
        return self 
                
    @api.multi
    def di_action_grille_vente(self):
        self.ensure_one()        
         
        view=self.env.ref('difodoo_ventes.di_grille_vente_wiz').id
        #       
      
        ctx= {                
                'di_model':'sale.order',   
                'di_order': self                           
            }
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'name': 'Grille de vente',
            'res_model': 'di.grille.vente.wiz',
            'views': [(view, 'form')],
            'view_id': view,                        
            'target': 'new',
            'multi':'False',
            'id':'di_action_grille_vente_wiz',
            'key2':'client_action_multi',
            'context': ctx            
        }
        
    @api.multi
    def di_action_supp_lig_zero(self):
        self.ensure_one()        
         
        view=self.env.ref('difodoo_ventes.di_supp_lig_zero_wiz').id
        #       
      
        ctx= {                
                'di_model':'sale.order',   
                'di_order': self                           
            }
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'name': 'Suppression lignes à 0',
            'res_model': 'di.supp.lig.zero.wiz',
            'views': [(view, 'form')],
            'view_id': view,                        
            'target': 'new',
            'multi':'False',
            'id':'di_action_supp_lig_zero_wiz',
            'key2':'client_action_multi',
            'context': ctx            
        }
            
    @api.model    
    def di_avec_lignes_mt_zero(self,id):         
        lines = False        
        order = self.env['sale.order'].browse(id)
        if order.state == 'draft' :                
            lines = self.env['sale.order.line'].search(['&', ('order_id', '=', id), ('price_subtotal', '=', 0.0), ('display_type', 'not in', ('line_section','line_note'))])        
            if lines:
                return True        
        return False
    
    @api.model    
    def di_avec_lignes_a_zero(self,id):         
        lines = False        
        order = self.env['sale.order'].browse(id)
        if order.state == 'draft' :                
            lines = self.env['sale.order.line'].search(['&', ('order_id', '=', id), ('product_uom_qty', '=', 0.0), ('display_type', 'not in', ('line_section','line_note'))])        
            if lines:
                return True        
        return False
     
    @api.model
    def di_supprimer_ligne_a_zero(self,id):        
        lines = False
        order = self.env['sale.order'].browse(id)
        if order.state == 'draft' :        
            lines = self.env['sale.order.line'].search(['&', ('order_id', '=', id), ('product_uom_qty', '=', 0.0)])
            if lines:                            
                order.write({'order_line': [(2, line.id, False) for line in lines]})                
                return True
        return False
             
    
    @api.model
    def create(self, vals):     
                                                    
        cde = super(SaleOrder, self).create(vals)
        lines = False
        for order in cde:    
#             if order.state == 'draft' :                                    
#                 lines = self.env['sale.order.line'].search(['&', ('order_id', '=', order.id), ('product_uom_qty', '=', 0.0)])                
#                 order.write({'order_line': [(2, line.id, False) for line in lines]})
            if order.di_nbex==0: 
                if order.partner_id:                
                    order.write({'di_nbex': order.partner_id.di_nbex_cde})
        return cde

     
#     @api.multi    # morvan, on n'est pas en suppression de ligne mais en suppression de commande (SaleOrder), déplacement dans SaleOrderLine
#     def unlink(self):        
#         self.get_delivery_price() # on recalcul le prix du transport si on supprime une ligne
#         res = super(SaleOrder, self).unlink()
#         return res
       
    
    @api.multi
    def write(self, vals):        
        res = super(SaleOrder, self).write(vals)   
        lines = False     
        for order in self:    
#             if order.state == 'draft' :   
# #                 order.di_supp_lig_zero()                                 
#                 lines = self.env['sale.order.line'].search(['&', ('order_id', '=', order.id), ('product_uom_qty', '=', 0.0)])                               
#                 super(SaleOrder, order).write({'order_line': [(2, line.id, False) for line in lines]})
            #ajout ligne transport
            if order.carrier_id and order.state in ("draft","sent") and order.delivery_rating_success:                
                order.set_delivery_line()
        return res
    
    
    @api.depends('state', 'order_line.invoice_status')
    def _get_invoiced(self):
        """
        Surcharge pour ne pas mettre le status facturé pour les commandes vides 
        """
        super(SaleOrder, self)._get_invoiced()
        for order in self:                        
            if not order.order_line:
                invoice_status = 'no'                            
                order.update({                
                    'invoice_status': invoice_status
                })
                
                

    @api.multi
    @api.onchange('partner_id')
    def onchange_partner_id(self):
        result=super(SaleOrder, self).onchange_partner_id()
        self.di_tournee = self.partner_id.di_tournee
        self.di_rangtournee = self.partner_id.di_rangtournee         
        return result
    
    @api.depends('order_line')
    def _compute_di_nbpal_nbcol(self):
        for order in self:
            wnbpal = sum(line.di_nb_palette for line in order.order_line)
            wnbcol = sum(line.di_nb_colis for line in order.order_line)
            order.di_nbpal = wnbpal
            order.di_nbcol = ceil(wnbcol)

    @api.multi
    def action_invoice_create(self, grouped=False, final=False):
        #copie standard
        """
        Create the invoice associated to the SO.
        :param grouped: if True, invoices are grouped by SO id. If False, invoices are grouped by
                        (partner_invoice_id, currency)
        :param final: if True, refunds will be generated if necessary
        :returns: list of created invoices
        """
        inv_obj = self.env['account.invoice']
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        invoices = {}
        references = {}
        invoices_origin = {}
        invoices_name = {}

        for order in self:
            group_key = order.id if grouped else (order.partner_invoice_id.id, order.currency_id.id)

            # We only want to create sections that have at least one invoiceable line
            pending_section = None

            for line in order.order_line:
                if line.display_type == 'line_section':
                    pending_section = line
                    continue
                if float_is_zero(line.qty_to_invoice, precision_digits=precision):
                    continue
                if group_key not in invoices:
                    inv_data = order._prepare_invoice()
                    invoice = inv_obj.create(inv_data)
                    references[invoice] = order
                    invoices[group_key] = invoice
                    invoices_origin[group_key] = [invoice.origin]
                    invoices_name[group_key] = [invoice.name]
                elif group_key in invoices:
                    if order.name not in invoices_origin[group_key]:
                        invoices_origin[group_key].append(order.name)
                    if order.client_order_ref and order.client_order_ref not in invoices_name[group_key]:
                        invoices_name[group_key].append(order.client_order_ref)

                if line.qty_to_invoice > 0 or (line.qty_to_invoice < 0 and final):
                    if pending_section:
                        pending_section.invoice_line_create(invoices[group_key].id, pending_section.qty_to_invoice)
                        pending_section = None
                    line.invoice_line_create(invoices[group_key].id, line.qty_to_invoice)

            if references.get(invoices.get(group_key)):
                if order not in references[invoices[group_key]]:
                    references[invoices[group_key]] |= order

        for group_key in invoices:
            invoices[group_key].write({'name': ', '.join(invoices_name[group_key]),
                                       'origin': ', '.join(invoices_origin[group_key])})
            sale_orders = references[invoices[group_key]]
            if len(sale_orders) == 1:
                invoices[group_key].reference = sale_orders.reference

        if not invoices:
            raise UserError(_('There is no invoiceable line. If a product has a Delivered quantities invoicing policy, please make sure that a quantity has been delivered.'))

        for invoice in invoices.values():
            invoice.compute_taxes()
            if not invoice.invoice_line_ids:
                raise UserError(_('There is no invoiceable line. If a product has a Delivered quantities invoicing policy, please make sure that a quantity has been delivered.'))
            # If invoice is negative, do a refund invoice instead
            if invoice.amount_total < 0:
                invoice.type = 'out_refund'
                for line in invoice.invoice_line_ids:
                    #difodoo
                    line.di_nb_colis = - line.di_nb_colis
                    line.di_nb_pieces = - line.di_nb_pieces
                    line.di_nb_palette = - line.di_nb_palette
                    line.di_poib = - line.di_poib
                    line.di_poin = - line.di_poin
                    line.di_qte_un_saisie = - line.di_qte_un_saisie
                    #fin difodoo
                    line.quantity = -line.quantity
            # Use additional field helper function (for account extensions)
            for line in invoice.invoice_line_ids:
                line._set_additional_fields(invoice)
            # Necessary to force computation of taxes. In account_invoice, they are triggered
            # by onchanges, which are not triggered when doing a create.
            invoice.compute_taxes()
            # Idem for partner
            so_payment_term_id = invoice.payment_term_id.id
            invoice._onchange_partner_id()
            # To keep the payment terms set on the SO
            invoice.payment_term_id = so_payment_term_id
            invoice.message_post_with_view('mail.message_origin_link',
                values={'self': invoice, 'origin': references[invoice]},
                subtype_id=self.env.ref('mail.mt_note').id)
        return [inv.id for inv in invoices.values()]