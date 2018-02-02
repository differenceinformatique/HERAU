# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, float_compare
from datetime import datetime, timedelta
from odoo import api, fields, models, _
from odoo.exceptions import UserError

class DiInheritedSaleOrderLine(models.Model):
    _inherit = "sale.order.line"
    
    di_qte_un_saisie = fields.Float(string='Quantité en unité de saisie')
    di_un_saisie     = fields.Selection([("PIECE", "Pièce"), ("COLIS", "Colis"),("PALETTE", "Palette"),("POIDS","Poids")], string="Unité de saisie")
    di_type_palette  = fields.Many2one('product.packaging', string='Palette') 
    di_nb_pieces     = fields.Integer(string='Nb pièces',compute="_compute_qte_aff",store=True)
    di_nb_colis      = fields.Integer(string='Nb colis',compute="_compute_qte_aff",store=True)
    di_nb_palette    = fields.Float(string='Nb palettes',compute="_compute_qte_aff",store=True)
    di_poin          = fields.Float(string='Poids net',compute="_compute_qte_aff",store=True)
    di_poib          = fields.Float(string='Poids brut')
    di_tare          = fields.Float(string='Tare')
        
    @api.one
    @api.depends('di_qte_un_saisie', 'di_un_saisie','di_type_palette','di_poib','di_tare','product_packaging')
    def _compute_qte_aff(self):
        if self.di_un_saisie == "PIECE":
            self.di_nb_pieces = self.di_qte_un_saisie            
            if self.product_packaging.qty != 0.0 :
                self.di_nb_colis = self.product_uom_qty / self.product_packaging.qty
            else:      
                self.di_nb_colis = self.product_uom_qty             
            if self.di_type_palette.di_qte_cond_inf != 0.0:
                self.di_nb_palette = self.di_nb_colis / self.di_type_palette.di_qte_cond_inf
            else:
                self.di_nb_palette = self.di_nb_colis
            self.di_poin = self.product_uom_qty * self.product_id.weight             
                  
        elif self.di_un_saisie == "COLIS":
            self.di_nb_colis = self.di_qte_un_saisie            
            self.di_nb_pieces = self.product_packaging.di_qte_cond_inf * self.di_nb_colis
            if self.di_type_palette.di_qte_cond_inf !=0.0:                
                self.di_nb_palette = self.di_nb_colis / self.di_type_palette.di_qte_cond_inf
            else:
                self.di_nb_palette = self.di_nb_colis
            self.di_poin = self.product_uom_qty * self.product_id.weight             
                                 
        elif self.di_un_saisie == "PALETTE":            
            self.di_nb_palette = self.di_qte_un_saisie
            if self.di_type_palette.di_qte_cond_inf!=0.0:
                self.di_nb_colis = self.di_nb_palette / self.di_type_palette.di_qte_cond_inf
            else:
                self.di_nb_colis = self.di_nb_palette
            self.di_nb_pieces = self.product_packaging.di_qte_cond_inf * self.di_nb_colis            
            self.di_poin = self.product_uom_qty * self.product_id.weight             
            
        elif self.di_un_saisie == "POIDS":
            self.di_poin = self.di_qte_un_saisie                        
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
    
    @api.multi
    @api.onchange('product_id')
    def _di_charger_valeur_par_defaut(self):
        if self.product_id.id != False:
            self.di_un_saisie = self.product_id.di_un_saisie
            self.di_type_palette = self.product_id.di_type_palette
            self.product_packaging = self.product_id.di_type_colis            
    
    @api.multi
    @api.onchange('di_qte_un_saisie', 'di_un_saisie','di_type_palette','di_poib','di_tare','product_packaging')
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
    
#     @api.multi    
#     def _di_recalcule_nb_colis(self,vals):
#         nbcolis = fields.Integer()
#         nbcolis = 3
#         return nbcolis
#     
#     @api.model
#     def create(self, vals):                    
#         vals["di_nb_colis"] = self._di_recalcule_nb_colis(vals)
#         vals["di_nb_pieces"] = 4
#         vals["di_nb_palette"] = 1
#         vals["di_poin"] = 8
#         res = super(DiInheritedSaleOrderLine, self).create(vals)                           
#         return res