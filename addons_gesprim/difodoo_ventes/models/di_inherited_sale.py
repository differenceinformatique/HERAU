
# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, float_compare
from datetime import datetime, timedelta
from odoo.exceptions import UserError
# from addons import sale,account,stock,sale_stock 
# from difodoo.addons_gesprim.difodoo_ventes.models.di_outils import * 
from difodoo.addons_gesprim.difodoo_ventes.models.di_outils import di_recherche_prix_unitaire
from math import *


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"
    
    modifparprg = False
    
    di_qte_un_saisie= fields.Float(string='Quantité en unité de saisie',store=True)
    di_un_saisie    = fields.Selection([("PIECE", "Pièce"), ("COLIS", "Colis"),("PALETTE", "Palette"),("KG","Kg")], string="Unité de saisie",store=True)
    di_type_palette_id  = fields.Many2one('product.packaging', string='Palette') 
    di_nb_pieces    = fields.Integer(string='Nb pièces' ,compute="_compute_qte_aff",store=True)
    di_nb_colis     = fields.Integer(string='Nb colis',compute="_compute_qte_aff",store=True)
    di_nb_palette   = fields.Float(string='Nb palettes',compute="_compute_qte_aff",store=True)
    di_poin         = fields.Float(string='Poids net',compute="_compute_qte_aff",store=True)
    di_poib         = fields.Float(string='Poids brut',store=True)
    di_tare         = fields.Float(string='Tare',store=True)
    di_un_prix      = fields.Selection([("PIECE", "Pièce"), ("COLIS", "Colis"),("PALETTE", "Palette"),("KG","Kg")], string="Unité de prix",store=True)
    di_flg_modif_uom = fields.Boolean(store=True)

    di_qte_un_saisie_liv = fields.Float(string='Quantité livrée en unité de saisie')
    di_un_saisie_liv     = fields.Selection([("PIECE", "Pièce"), ("COLIS", "Colis"),("PALETTE", "Palette"),("KG","Kg")], string="Unité de saisie livrée")
    di_type_palette_liv_id  = fields.Many2one('product.packaging', string='Palette livrée') 
    di_nb_pieces_liv     = fields.Integer(string='Nb pièces livrées')
    di_nb_colis_liv      = fields.Integer(string='Nb colis livrés')
    di_nb_palette_liv    = fields.Float(string='Nb palettes livrées')
    di_poin_liv          = fields.Float(string='Poids net livré')
    di_poib_liv          = fields.Float(string='Poids brut livré')
    di_tare_liv          = fields.Float(string='Tare livrée')
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
    
    di_spe_saisissable = fields.Boolean(string='Champs spé saisissables',default=False,compute='_di_compute_spe_saisissable',store=True)
                                         
    @api.one
    @api.depends('product_id.di_spe_saisissable')
    def _di_compute_spe_saisissable(self):        
        self.di_spe_saisissable =self.product_id.di_spe_saisissable
     

    @api.depends('product_uom_qty', 'discount', 'price_unit', 'tax_id','di_qte_un_saisie','di_nb_pieces','di_nb_colis','di_nb_palette','di_poin','di_poib','di_tare','di_un_prix')
    def _compute_amount(self):
        """
        Compute the amounts of the SO line.
        """
        for line in self:
            price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
            
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
            if self.product_id.id != False:
                self.di_un_saisie = self.product_id.di_un_saisie
                self.di_type_palette_id = self.product_id.di_type_palette_id
                self.product_packaging = self.product_id.di_type_colis_id    
                self.di_un_prix = self.product_id.di_un_prix        


    @api.multi
    @api.onchange('product_id')
    def product_id_change(self):
        result=super(SaleOrderLine, self).product_id_change()
        #surcharge de la procédure pour recalculer le prix car elle est appelée après _di_changer_prix quand on modifie l'article
        vals = {}
        if self.product_id and self.di_un_prix:
#             if vals.get("price_unit"):
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
                
            vals['price_unit'] = di_recherche_prix_unitaire(self,self.price_unit,self.order_id.partner_id,self.product_id,self.di_un_prix,di_qte_prix,self.order_id.date_order)
            self.update(vals)       
        return result
    
    @api.onchange('product_uom', 'product_uom_qty')
    def product_uom_change(self):
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
            self.price_unit = di_recherche_prix_unitaire(self,self.price_unit,self.order_id.partner_id,self.product_id,self.di_un_prix,di_qte_prix,self.order_id.date_order)       
                
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
                line.price_unit = di_recherche_prix_unitaire(self,line.price_unit,line.order_id.partner_id,line.product_id,line.di_un_prix,di_qte_prix,line.order_id.date_order)
    @api.multi
    @api.onchange('di_poib')
    def _di_recalcule_tare(self):
        if self.ensure_one():
            self.di_tare = self.di_poib - self.di_poin
            
    @api.multi    
    @api.onchange('product_uom_qty')
    def _di_modif_qte_un_mesure(self):
        if self.ensure_one():
            if SaleOrderLine.modifparprg == False:
                if self.product_uom:
                    if self.product_uom.name.lower() == 'kg':
                        self.di_poin=self.product_uom_qty * self.product_id.weight
                        self.di_poib = self.di_poin + self.di_tare
                    elif self.product_uom.name.lower() != 'kg':    
                        if self.product_id.di_get_type_piece().qty != 0.0:
                            self.di_nb_pieces = ceil(self.product_uom_qty/self.product_id.di_get_type_piece().qty)
                        else:
                            self.di_nb_pieces = ceil(self.product_uom_qty)                                
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
                    self.di_flg_modif_uom = True
            SaleOrderLine.modifparprg=False
    
    @api.multi    
    @api.onchange('di_qte_un_saisie', 'di_un_saisie','di_type_palette_id','di_tare','product_packaging')
    def _di_recalcule_quantites(self):
        if self.ensure_one():
            if self.di_flg_modif_uom == False:
                SaleOrderLine.modifparprg=True
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
                        self.di_nb_colis = ceil(self.di_nb_palette / self.di_type_palette_id.di_qte_cond_inf)
                    else:
                        self.di_nb_colis = ceil(self.di_nb_palette)
                    self.di_nb_pieces = ceil(self.product_packaging.di_qte_cond_inf * self.di_nb_colis)
                    self.product_uom_qty = self.product_packaging.qty * self.di_nb_colis
                    self.di_poin = self.product_uom_qty * self.product_id.weight 
                    self.di_poib = self.di_poin + self.di_tare
                    
                elif self.di_un_saisie == "KG":
                    self.di_poin = self.di_qte_un_saisie
                    self.di_poib = self.di_poin + self.di_tare
                    self.product_uom_qty = self.di_poin
                    if self.product_packaging.qty !=0.0:
                        self.di_nb_colis = ceil(self.product_uom_qty / self.product_packaging.qty)
                    else:
                        self.di_nb_colis = ceil(self.product_uom_qty)
                    if self.di_type_palette_id.di_qte_cond_inf !=0.0:    
                        self.di_nb_palette = self.di_nb_colis / self.di_type_palette_id.di_qte_cond_inf
                    else:  
                        self.di_nb_palette = self.di_nb_colis
                    self.di_nb_pieces = ceil(self.product_packaging.di_qte_cond_inf * self.di_nb_colis)
                    
                else:
                    self.di_poin = self.di_qte_un_saisie
                    self.di_poib = self.di_poin + self.di_tare
                    self.product_uom_qty = self.di_poin
                    if self.product_packaging.qty !=0.0:
                        self.di_nb_colis = ceil(self.product_uom_qty / self.product_packaging.qty)
                    else:
                        self.di_nb_colis = ceil(self.product_uom_qty)
                    if self.di_type_palette_id.di_qte_cond_inf !=0.0:    
                        self.di_nb_palette = self.di_nb_colis / self.di_type_palette_id.di_qte_cond_inf
                    else:  
                        self.di_nb_palette = self.di_nb_colis
                    self.di_nb_pieces = ceil(self.product_packaging.di_qte_cond_inf * self.di_nb_colis)
                
    @api.one
    @api.depends('di_qte_un_saisie', 'di_un_saisie','di_type_palette_id','di_tare','product_packaging')
    def _compute_qte_aff(self):
        #if self.ensure_one():
        
        if self.di_flg_modif_uom == False:
            if self.di_un_saisie == "PIECE":
                self.di_nb_pieces = ceil(self.di_qte_un_saisie)            
                if self.product_packaging.qty != 0.0 :
                    self.di_nb_colis = ceil(self.product_uom_qty / self.product_packaging.qty)
                else:      
                    self.di_nb_colis = ceil(self.product_uom_qty)             
                if self.di_type_palette_id.di_qte_cond_inf != 0.0:
                    self.di_nb_palette = self.di_nb_colis / self.di_type_palette_id.di_qte_cond_inf
                else:
                    self.di_nb_palette = self.di_nb_colis
                self.di_poin = self.product_uom_qty * self.product_id.weight             
                        
            elif self.di_un_saisie == "COLIS":
                self.di_nb_colis = ceil(self.di_qte_un_saisie)            
                self.di_nb_pieces = ceil(self.product_packaging.di_qte_cond_inf * self.di_nb_colis)
                if self.di_type_palette_id.di_qte_cond_inf !=0.0:                
                    self.di_nb_palette = self.di_nb_colis / self.di_type_palette_id.di_qte_cond_inf
                else:
                    self.di_nb_palette = self.di_nb_colis
                self.di_poin = self.product_uom_qty * self.product_id.weight             
                                       
            elif self.di_un_saisie == "PALETTE":            
                self.di_nb_palette = self.di_qte_un_saisie
                if self.di_type_palette_id.di_qte_cond_inf!=0.0:
                    self.di_nb_colis = ceil(self.di_nb_palette / self.di_type_palette_id.di_qte_cond_inf)
                else:
                    self.di_nb_colis = ceil(self.di_nb_palette)
                self.di_nb_pieces = ceil(self.product_packaging.di_qte_cond_inf * self.di_nb_colis)            
                self.di_poin = self.product_uom_qty * self.product_id.weight             
                  
            elif self.di_un_saisie == "KG":
                self.di_poin = self.di_qte_un_saisie                        
                if self.product_packaging.qty !=0.0:
                    self.di_nb_colis = ceil(self.product_uom_qty / self.product_packaging.qty)
                else:
                    self.di_nb_colis = ceil(self.product_uom_qty)
                if self.di_type_palette_id.di_qte_cond_inf !=0.0:    
                    self.di_nb_palette = self.di_nb_colis / self.di_type_palette_id.di_qte_cond_inf
                else:  
                    self.di_nb_palette = self.di_nb_colis
                self.di_nb_pieces = ceil(self.product_packaging.di_qte_cond_inf * self.di_nb_colis)
                  
            else:
                self.di_poin = self.di_qte_un_saisie            
                self.product_uom_qty = self.di_poin
                if self.product_packaging.qty !=0.0:
                    self.di_nb_colis = ceil(self.product_uom_qty / self.product_packaging.qty)
                else:
                    self.di_nb_colis = ceil(self.product_uom_qty)
                if self.di_type_palette_id.di_qte_cond_inf !=0.0:    
                    self.di_nb_palette = self.di_nb_colis / self.di_type_palette_id.di_qte_cond_inf
                else:  
                    self.di_nb_palette = self.di_nb_colis
                self.di_nb_pieces = ceil(self.product_packaging.di_qte_cond_inf * self.di_nb_colis)
        else:           
            if self.product_id.di_get_type_piece().qty != 0.0:
                self.di_nb_pieces = ceil(self.product_uom_qty/self.product_id.di_get_type_piece().qty)
            else:
                self.di_nb_pieces = ceil(self.product_uom_qty)                                
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
            
    @api.multi
    def _check_package(self):    
        #surcharge pour enlever le contrôle sur le nombre d'unités saisies en fonction du colis choisi    
        return {}
        
    @api.onchange('product_uom_qty', 'product_uom', 'route_id')
    def _onchange_product_id_check_availability(self):
        #surcharge pour enlever la remise à 0 de product_packaging
        if self.product_id.type == 'product':
            precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
            product = self.product_id.with_context(warehouse=self.order_id.warehouse_id.id)
            product_qty = self.product_uom._compute_quantity(self.product_uom_qty, self.product_id.uom_id)
            if float_compare(product.virtual_available, product_qty, precision_digits=precision) == -1:
                is_available = self._check_routing()
                if not is_available:
                    message =  _('You plan to sell %s %s but you only have %s %s available in %s warehouse.') % \
                            (self.product_uom_qty, self.product_uom.name, product.virtual_available, product.uom_id.name, self.order_id.warehouse_id.name)
                    # We check if some products are available in other warehouses.
                    if float_compare(product.virtual_available, self.product_id.virtual_available, precision_digits=precision) == -1:
                        message += _('\nThere are %s %s available accross all warehouses.') % \
                                (self.product_id.virtual_available, product.uom_id.name)

                    warning_mess = {
                        'title': _('Not enough inventory!'),
                        'message' : message
                    }
                    return {'warning': warning_mess}
        return {}
    
    @api.depends('di_qte_un_saisie_fac', 'di_qte_un_saisie_liv', 'di_qte_un_saisie', 'order_id.state')
    def _get_to_invoice_qty(self):
        
        """
        Compute the quantity to invoice. If the invoice policy is order, the quantity to invoice is
        calculated from the ordered quantity. Otherwise, the quantity delivered is used.
        """
        for line in self:
            if line.order_id.state in ['sale', 'done']:
                if line.product_id.invoice_policy == 'order':
                    line.di_qte_a_facturer_un_saisie = line.di_qte_un_saisie - line.di_qte_un_saisie_fac
                else:
                    line.di_qte_a_facturer_un_saisie = line.di_qte_un_saisie_liv - line.di_qte_un_saisie_fac
            else:
                line.di_qte_a_facturer_un_saisie = 0
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
            for invoice_line in line.invoice_lines:
                if invoice_line.invoice_id.state != 'cancel':
                    if invoice_line.invoice_id.type == 'out_invoice':
                        qty_invoiced += invoice_line.di_qte_un_saisie
                    elif invoice_line.invoice_id.type == 'out_refund':
                        qty_invoiced -= invoice_line.di_qte_un_saisie
            line.di_qte_un_saisie_fac = qty_invoiced
        super(SaleOrderLine, self)._get_invoice_qty()
  
class SaleOrder(models.Model):
    _inherit = "sale.order"
    di_period_fact = fields.Selection(string="Périodicité de Facturation", related='partner_id.di_period_fact')#,store=True)
    di_regr_fact = fields.Boolean(string="Regroupement sur Facture", related='partner_id.di_regr_fact')#,store=True)
    di_livdt = fields.Date(string='Date de livraison', copy=False, help="Date de livraison souhaitée",
                           default=lambda wdate : datetime.today().date()+timedelta(days=1))
    di_prepdt = fields.Date(string='Date de préparation', copy=False, help="Date de préparation",
                           default=lambda wdate : datetime.today().date())
     
    @api.multi
    @api.onchange('di_livdt')
    def modif_livdt(self):
        if datetime.strptime(self.di_livdt,'%Y-%m-%d').date()<datetime.today().date():
            return {'warning': {'Erreur date livraison': _('Error'), 'message': _('La date de livraison ne peut être inférieure à la date du jour !'),},}       
        self.di_prepdt = datetime.strptime(self.di_livdt,'%Y-%m-%d').date() + timedelta(days=-1)
        if datetime.strptime(self.di_prepdt,'%Y-%m-%d').date()<datetime.today().date():
            self.di_prepdt=datetime.today().date()
        self.requested_date = datetime.strptime(self.di_livdt,'%Y-%m-%d')
     
    @api.multi
    @api.onchange('di_prepdt')
    def modif_prepdt(self):
        if datetime.strptime(self.di_prepdt,'%Y-%m-%d').date()<datetime.today().date():
            return {'warning': {'Erreur date préparation': _('Error'), 'message': _('La date de préparation ne peut être inférieure à la date du jour !'),},}
        self.di_livdt = datetime.strptime(self.di_prepdt,'%Y-%m-%d').date() + timedelta(days=1)
        self.requested_date = datetime.strptime(self.di_livdt,'%Y-%m-%d')
     
    def _force_lines_to_invoice_policy_order(self):
        super(SaleOrder, self)._force_lines_to_invoice_policy_order()
        for line in self.order_line:
            if self.state in ['sale', 'done']:
                line.di_qte_a_facturer_un_saisie = line.di_qte_un_saisie - line.di_qte_un_saisie_fac
            else:
                line.di_qte_a_facturer_un_saisie = 0    
#     @api.model
#     def write(self, vals):                
#         result = super(SaleOrder, self).write(vals)
#         self.action_confirm()
#         return result