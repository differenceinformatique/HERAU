# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, float_compare
from datetime import datetime, timedelta
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from addons import sale,account,stock,sale_stock 
from difodoo import *

class DiInheritedSaleOrderLine(models.Model):
    _inherit = "sale.order.line"
    
    di_qte_un_saisie = fields.Float(string='Quantité en unité de saisie',store=True)
    di_un_saisie     = fields.Selection([("PIECE", "Pièce"), ("COLIS", "Colis"),("PALETTE", "Palette"),("POIDS","Poids")], string="Unité de saisie",store=True)
    di_type_palette  = fields.Many2one('product.packaging', string='Palette') 
    di_nb_pieces     = fields.Integer(string='Nb pièces' ,compute="_compute_qte_aff",store=True)
    di_nb_colis      = fields.Integer(string='Nb colis',compute="_compute_qte_aff",store=True)
    di_nb_palette    = fields.Float(string='Nb palettes',compute="_compute_qte_aff",store=True)
    di_poin          = fields.Float(string='Poids net',compute="_compute_qte_aff",store=True)
    di_poib          = fields.Float(string='Poids brut',store=True)
    di_tare          = fields.Float(string='Tare',store=True)

    di_qte_un_saisie_liv = fields.Float(string='Quantité livrée en unité de saisie')
    di_un_saisie_liv     = fields.Selection([("PIECE", "Pièce"), ("COLIS", "Colis"),("PALETTE", "Palette"),("POIDS","Poids")], string="Unité de saisie livrée")
    di_type_palette_liv  = fields.Many2one('product.packaging', string='Palette livrée') 
    di_nb_pieces_liv     = fields.Integer(string='Nb pièces livrées')
    di_nb_colis_liv      = fields.Integer(string='Nb colis livrés')
    di_nb_palette_liv    = fields.Float(string='Nb palettes livrées')
    di_poin_liv          = fields.Float(string='Poids net livré')
    di_poib_liv          = fields.Float(string='Poids brut livré')
    di_tare_liv          = fields.Float(string='Tare livrée')
    di_product_packaging_liv=fields.Many2one('product.packaging', string='Colis livré')
    
    di_qte_un_saisie_fac = fields.Float(string='Quantité facturée en unité de saisie',compute='_get_invoice_qty')
    di_un_saisie_fac     = fields.Selection([("PIECE", "Pièce"), ("COLIS", "Colis"),("PALETTE", "Palette"),("POIDS","Poids")], string="Unité de saisie facturés")
    di_type_palette_fac  = fields.Many2one('product.packaging', string='Palette facturée') 
    di_nb_pieces_fac     = fields.Integer(string='Nb pièces facturées')
    di_nb_colis_fac      = fields.Integer(string='Nb colis facturés')
    di_nb_palette_fac    = fields.Float(string='Nb palettes facturées')
    di_poin_fac          = fields.Float(string='Poids net facturé')
    di_poib_fac          = fields.Float(string='Poids brut facturé')
    di_tare_fac          = fields.Float(string='Tare facturée')
    di_product_packaging_fac=fields.Many2one('product.packaging', string='Colis facturé')
    
    di_qte_a_facturer_un_saisie = fields.Float(string='Quantité à facturer en unité de saisie',compute='_get_to_invoice_qty')
     
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
        super(DiInheritedSaleOrderLine, self)._get_to_invoice_qty()
                
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
        super(DiInheritedSaleOrderLine, self)._get_invoice_qty()
  
class DiInheritedSaleOrder(models.Model):
    _inherit = "sale.order"  
    
    def _force_lines_to_invoice_policy_order(self):
        super(DiInheritedSaleOrder, self)._force_lines_to_invoice_policy_order()
        for line in self.order_line:
            if self.state in ['sale', 'done']:
                line.di_qte_a_facturer_un_saisie = line.di_qte_un_saisie - line.di_qte_un_saisie_fac
            else:
                line.di_qte_a_facturer_un_saisie = 0