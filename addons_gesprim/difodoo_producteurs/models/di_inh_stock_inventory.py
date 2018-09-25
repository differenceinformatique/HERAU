# -*- coding: utf-8 -*-
from datetime import datetime,timedelta

from odoo import models, fields, api, _
from odoo.tools import float_utils
from math import ceil

class Inventory(models.Model):
    _inherit = "stock.inventory"
    di_type_inv    = fields.Selection([("std", "Standard"), ("retcons", "Retour consigne"),("appprod", "Apport producteur")], string="Type inventaire",default='std',store=True)
    
class InventoryLine(models.Model):
    _inherit = "stock.inventory.line"         
                   
    di_lot_prod = fields.Char(string="Lot producteur")
    
            
    def _get_move_values(self, qty, location_id, location_dest_id, out):
        #je dois surcharger en copiant le standard
        self.ensure_one()
        return {
            'name': _('INV:') + (self.inventory_id.name or ''),
            'product_id': self.product_id.id,
            'product_uom': self.product_uom_id.id,
            'product_uom_qty': qty,
            'date': self.inventory_id.date,
            'company_id': self.inventory_id.company_id.id,
            'inventory_id': self.inventory_id.id,
            'state': 'confirmed',
            'restrict_partner_id': self.partner_id.id,
            'location_id': location_id,
            'location_dest_id': location_dest_id,
            'move_line_ids': [(0, 0, {
                'product_id': self.product_id.id,
                'lot_id': self.prod_lot_id.id,
                #surcharge
                'lot_name':self.prodlot_name,
                #fin surcharge 
                'product_uom_qty': 0,  # bypass reservation here
                'product_uom_id': self.product_uom_id.id,
                'qty_done': qty,
                'package_id': out and self.package_id.id or False,
                'result_package_id': (not out) and self.package_id.id or False,
                'location_id': location_id,
                'location_dest_id': location_dest_id,
                'owner_id': self.partner_id.id,
                'di_lot_prod':self.di_lot_prod
            })]
        }
            
            
    def _di_get_move_values_col(self, qty, location_id, location_dest_id, out):
        #je dois surcharger en copiant le standard
        self.ensure_one()
        return {
            'name': _('INV:') + (self.inventory_id.name or ''),
            'product_id': self.product_id.id,
            'product_uom': self.product_uom_id.id,
            'product_uom_qty': 0.0,
            'date': self.inventory_id.date,
            'company_id': self.inventory_id.company_id.id,
            'inventory_id': self.inventory_id.id,
            'state': 'confirmed',
            'restrict_partner_id': self.partner_id.id,
            'location_id': location_id,
            'location_dest_id': location_dest_id,
            #surcharge                      
            'di_nb_colis': qty,            
            #fin surcharge                        
            'move_line_ids': [(0, 0, {
                'product_id': self.product_id.id,
                'lot_id': self.prod_lot_id.id,
                #surcharge
                'lot_name':self.prodlot_name,
                #fin surcharge 
                'product_uom_qty': 0,  # bypass reservation here
                'product_uom_id': self.product_uom_id.id,
                'qty_done': 1.0,
                'package_id': out and self.package_id.id or False,
                'result_package_id': (not out) and self.package_id.id or False,
                'location_id': location_id,
                'location_dest_id': location_dest_id,
                'owner_id': self.partner_id.id,
                #surcharge                            
                'di_nb_colis': qty,      
                'di_lot_prod':self.di_lot_prod          
                #fin surcharge
            })]
        }
        
    def _di_get_move_values_piece(self, qty, location_id, location_dest_id, out):
        #je dois surcharger en copiant le standard
        self.ensure_one()
        return {
            'name': _('INV:') + (self.inventory_id.name or ''),
            'product_id': self.product_id.id,
            'product_uom': self.product_uom_id.id,
            'product_uom_qty': 0.0,
            'date': self.inventory_id.date,
            'company_id': self.inventory_id.company_id.id,
            'inventory_id': self.inventory_id.id,
            'state': 'confirmed',
            'restrict_partner_id': self.partner_id.id,
            'location_id': location_id,
            'location_dest_id': location_dest_id,
            #surcharge                      
            'di_nb_pieces': qty,            
            #fin surcharge                        
            'move_line_ids': [(0, 0, {
                'product_id': self.product_id.id,
                'lot_id': self.prod_lot_id.id,
                #surcharge
                'lot_name':self.prodlot_name,
                #fin surcharge 
                'product_uom_qty': 0,  # bypass reservation here
                'product_uom_id': self.product_uom_id.id,
                'qty_done': 1.0,
                'package_id': out and self.package_id.id or False,
                'result_package_id': (not out) and self.package_id.id or False,
                'location_id': location_id,
                'location_dest_id': location_dest_id,
                'owner_id': self.partner_id.id,
                #surcharge                            
                'di_nb_pieces': qty,
                'di_lot_prod':self.di_lot_prod                
                #fin surcharge
            })]
        }
        
    def _di_get_move_values_poids(self, qty, location_id, location_dest_id, out):
        #je dois surcharger en copiant le standard
        self.ensure_one()
        return {
            'name': _('INV:') + (self.inventory_id.name or ''),
            'product_id': self.product_id.id,
            'product_uom': self.product_uom_id.id,
            'product_uom_qty': 0.0,
            'date': self.inventory_id.date,
            'company_id': self.inventory_id.company_id.id,
            'inventory_id': self.inventory_id.id,
            'state': 'confirmed',
            'restrict_partner_id': self.partner_id.id,
            'location_id': location_id,
            'location_dest_id': location_dest_id,
            #surcharge                      
            'di_poin': qty,            
            #fin surcharge                        
            'move_line_ids': [(0, 0, {
                'product_id': self.product_id.id,
                'lot_id': self.prod_lot_id.id,
                #surcharge
                'lot_name':self.prodlot_name,
                #fin surcharge 
                'product_uom_qty': 0,  # bypass reservation here
                'product_uom_id': self.product_uom_id.id,
                'qty_done': 1.0,
                'package_id': out and self.package_id.id or False,
                'result_package_id': (not out) and self.package_id.id or False,
                'location_id': location_id,
                'location_dest_id': location_dest_id,
                'owner_id': self.partner_id.id,
                #surcharge                            
                'di_poin': qty,
                'di_lot_prod':self.di_lot_prod                
                #fin surcharge
            })]
        }        
         
    def _di_get_move_values_pal(self, qty, location_id, location_dest_id, out):
        #je dois surcharger en copiant le standard
        self.ensure_one()
        return {
            'name': _('INV:') + (self.inventory_id.name or ''),
            'product_id': self.product_id.id,
            'product_uom': self.product_uom_id.id,
            'product_uom_qty': 0.0,
            'date': self.inventory_id.date,
            'company_id': self.inventory_id.company_id.id,
            'inventory_id': self.inventory_id.id,
            'state': 'confirmed',
            'restrict_partner_id': self.partner_id.id,
            'location_id': location_id,
            'location_dest_id': location_dest_id,
            #surcharge                      
            'di_nb_palette': qty,            
            #fin surcharge                        
            'move_line_ids': [(0, 0, {
                'product_id': self.product_id.id,
                'lot_id': self.prod_lot_id.id,
                #surcharge
                'lot_name':self.prodlot_name,
                #fin surcharge 
                'product_uom_qty': 0,  # bypass reservation here
                'product_uom_id': self.product_uom_id.id,
                'qty_done': 1.0,
                'package_id': out and self.package_id.id or False,
                'result_package_id': (not out) and self.package_id.id or False,
                'location_id': location_id,
                'location_dest_id': location_dest_id,
                'owner_id': self.partner_id.id,
                #surcharge                            
                'di_nb_palette': qty,
                'di_lot_prod':self.di_lot_prod                
                #fin surcharge
            })]
        }
