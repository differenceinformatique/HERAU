# -*- coding: utf-8 -*-
from odoo import api, fields, models
from datetime import timedelta, datetime
import io
# import os
import base64
# from ..models import di_outils
# from pip._internal import download
from odoo.tools import pycompat

class DiCloturerLots(models.TransientModel):
    _name = "di.cloturer.lots.wiz"
    _description = "Wizard clôture des lots"
        
    di_product_id = fields.Many2one('product.product',string="Article")
    di_lot  =   fields.Char("Lot", help=""" Mettre * pour prendre tous les lots de l'article sélectionné. """)
    
    art_debut = fields.Char(default=" ", string="Code Article Début")
    art_fin = fields.Char(default="ZZZZZZZZZZ", string="Code Article Fin")
    
    familles = fields.Many2many("product.category", string="Familles")
    
  
    @api.multi
    def cloturer_lots(self):
        self.ensure_one()  
        if self.di_product_id:            
            if self.di_lot == '*':
                lots = self.env['stock.production.lot'].search(['&',('di_fini', '=', False),('product_id','=',self.di_product_id.id)])
            else:
                lots = self.env['stock.production.lot'].search(['&',('di_fini', '=', False),('product_id','=',self.di_product_id.id),('name','=',self.di_lot)])
        else:
            if self.familles:
                lots = self.env['stock.production.lot'].search([('di_fini', '=', False)]).filtered(lambda l: l.product_id.categ_id in self.familles and l.product_id.name <= self.art_debut and l.product_id.name >= self.art_fin)
            else:                        
                lots = self.env['stock.production.lot'].search([('di_fini', '=', False)]).filtered(lambda l:  l.product_id.name <= self.art_debut and l.product_id.name >= self.art_fin)
                            
        
        for lot in lots:
            
            if lot.product_qty == 0.0:
                nbcol = 0.0
                nbpal= 0.0
                nbpiece = 0.0
                poin =0.0
                qte =0.0
                poib=0.0
                
                qtediff = 0.0
                (nbcol,nbpal,nbpiece,poin,qte,poib)= self.env['stock.move.line'].di_qte_spe_en_stock(lot.product_id,False,lot)
                if nbcol != 0.0 or nbpal != 0.0 or nbpiece != 0.0 or poin != 0.0 or poib != 0.0:                
                    locationinterne_id = self.env['stock.picking.type'].search([('code','=','incoming')], limit=1).default_location_dest_id.id
                    if nbcol > 0.0:
                        qtediff = qtediff - 1.0
                        vals = {
                                'name': "Clôture lot",
                                'product_id': lot.product_id.id,
                                'product_uom': lot.product_uom_id.id,
                                'product_uom_qty': 0.0,
                                'date': datetime.now(),
                                'company_id': self.env.user.company_id.id,                            
                                'state': 'done',                            
                                'location_id':  locationinterne_id,
                                'location_dest_id':  lot.product_id.property_stock_inventory.id,
                                #surcharge                      
                                'di_nb_colis': abs(nbcol),            
                                #fin surcharge                        
                                'move_line_ids': [(0, 0, {
                                    'product_id': lot.product_id.id,
                                    'lot_id': lot.id,
                                    'product_uom_qty': 0,  # bypass reservation here
                                    'product_uom_id': lot.product_uom_id.id,
                                    'qty_done': 1.0,                                                                
                                    'location_id': locationinterne_id,
                                    'location_dest_id':lot.product_id.property_stock_inventory.id,                               
                                    #surcharge                            
                                    'di_nb_colis': abs(nbcol),     
#                                     'di_perte': True           
                                    #fin surcharge
                                })]
                            }
                        self.env['stock.move'].create(vals)
                    elif nbcol < 0.0:
                        qtediff = qtediff + 1.0
                        vals = {
                                'name': "Clôture lot",
                                'product_id': lot.product_id.id,
                                'product_uom': lot.product_uom_id.id,
                                'product_uom_qty': 0.0,
                                'date': datetime.now(),
                                'company_id': self.env.user.company_id.id,                            
                                'state': 'done',                            
                                'location_id': lot.product_id.property_stock_inventory.id,
                                'location_dest_id': locationinterne_id,
                                #surcharge                      
                                'di_nb_colis': abs(nbcol),            
                                #fin surcharge                        
                                'move_line_ids': [(0, 0, {
                                    'product_id': lot.product_id.id,
                                    'lot_id': lot.id,
                                    'product_uom_qty': 0,  # bypass reservation here
                                    'product_uom_id': lot.product_uom_id.id,
                                    'qty_done': 1.0,                                                                
                                    'location_id':lot.product_id.property_stock_inventory.id,
                                    'location_dest_id': locationinterne_id,                                
                                    #surcharge                            
                                    'di_nb_colis': abs(nbcol),     
#                                     'di_perte': True           
                                    #fin surcharge
                                })]
                            }
                        self.env['stock.move'].create(vals)
                    
                    if nbpal > 0.0:
                        qtediff = qtediff - 1.0
                        vals = {
                                'name': "Clôture lot",
                                'product_id': lot.product_id.id,
                                'product_uom': lot.product_uom_id.id,
                                'product_uom_qty': 0.0,
                                'date': datetime.now(),
                                'company_id': self.env.user.company_id.id,                            
                                'state': 'done',                            
                                'location_id':  locationinterne_id,
                                'location_dest_id':  lot.product_id.property_stock_inventory.id,
                                #surcharge                      
                                'di_nb_palette': abs(nbpal),            
                                #fin surcharge                        
                                'move_line_ids': [(0, 0, {
                                    'product_id': lot.product_id.id,
                                    'lot_id': lot.id,
                                    'product_uom_qty': 0,  # bypass reservation here
                                    'product_uom_id': lot.product_uom_id.id,
                                    'qty_done': 1.0,                                                                
                                    'location_id': locationinterne_id,
                                    'location_dest_id':lot.product_id.property_stock_inventory.id,                               
                                    #surcharge                            
                                    'di_nb_palette': abs(nbpal),     
#                                     'di_perte': True           
                                    #fin surcharge
                                })]
                            }
                        self.env['stock.move'].create(vals)
                    elif nbpal < 0.0:
                        qtediff = qtediff + 1.0
                        vals = {
                                'name': "Clôture lot",
                                'product_id': lot.product_id.id,
                                'product_uom': lot.product_uom_id.id,
                                'product_uom_qty': 0.0,
                                'date': datetime.now(),
                                'company_id': self.env.user.company_id.id,                            
                                'state': 'done',                            
                                'location_id': lot.product_id.property_stock_inventory.id,
                                'location_dest_id': locationinterne_id,
                                #surcharge                      
                                'di_nb_palette': abs(nbpal),            
                                #fin surcharge                        
                                'move_line_ids': [(0, 0, {
                                    'product_id': lot.product_id.id,
                                    'lot_id': lot.id,
                                    'product_uom_qty': 0,  # bypass reservation here
                                    'product_uom_id': lot.product_uom_id.id,
                                    'qty_done': 1.0,                                                                
                                    'location_id':lot.product_id.property_stock_inventory.id,
                                    'location_dest_id': locationinterne_id,                                
                                    #surcharge                            
                                    'di_nb_palette': abs(nbpal),     
#                                     'di_perte': True           
                                    #fin surcharge
                                })]
                            }
                        self.env['stock.move'].create(vals)
                    
                    if nbpiece > 0.0:
                        qtediff = qtediff - 1.0
                        vals = {
                                'name': "Clôture lot",
                                'product_id': lot.product_id.id,
                                'product_uom': lot.product_uom_id.id,
                                'product_uom_qty': 0.0,
                                'date': datetime.now(),
                                'company_id': self.env.user.company_id.id,                            
                                'state': 'done',                            
                                'location_id':  locationinterne_id,
                                'location_dest_id':  lot.product_id.property_stock_inventory.id,
                                #surcharge                      
                                'di_nb_pieces': abs(nbpiece),            
                                #fin surcharge                        
                                'move_line_ids': [(0, 0, {
                                    'product_id': lot.product_id.id,
                                    'lot_id': lot.id,
                                    'product_uom_qty': 0,  # bypass reservation here
                                    'product_uom_id': lot.product_uom_id.id,
                                    'qty_done': 1.0,                                                                
                                    'location_id': locationinterne_id,
                                    'location_dest_id':lot.product_id.property_stock_inventory.id,                               
                                    #surcharge                            
                                    'di_nb_pieces': abs(nbpiece),     
#                                     'di_perte': True           
                                    #fin surcharge
                                })]
                            }
                        self.env['stock.move'].create(vals)
                    elif nbpiece < 0.0:
                        qtediff = qtediff + 1.0
                        vals = {
                                'name': "Clôture lot",
                                'product_id': lot.product_id.id,
                                'product_uom': lot.product_uom_id.id,
                                'product_uom_qty': 0.0,
                                'date': datetime.now(),
                                'company_id': self.env.user.company_id.id,                            
                                'state': 'done',                            
                                'location_id': lot.product_id.property_stock_inventory.id,
                                'location_dest_id': locationinterne_id,
                                #surcharge                      
                                'di_nb_pieces': abs(nbpiece),            
                                #fin surcharge                        
                                'move_line_ids': [(0, 0, {
                                    'product_id': lot.product_id.id,
                                    'lot_id': lot.id,
                                    'product_uom_qty': 0,  # bypass reservation here
                                    'product_uom_id': lot.product_uom_id.id,
                                    'qty_done': 1.0,                                                                
                                    'location_id':lot.product_id.property_stock_inventory.id,
                                    'location_dest_id': locationinterne_id,                                
                                    #surcharge                            
                                    'di_nb_pieces': abs(nbpiece),     
#                                     'di_perte': True           
                                    #fin surcharge
                                })]
                            }
                        self.env['stock.move'].create(vals)
                    
                    if poin > 0.0:
                        qtediff = qtediff - 1.0
                        vals = {
                                'name': "Clôture lot",
                                'product_id': lot.product_id.id,
                                'product_uom': lot.product_uom_id.id,
                                'product_uom_qty': 0.0,
                                'date': datetime.now(),
                                'company_id': self.env.user.company_id.id,                            
                                'state': 'done',                            
                                'location_id':  locationinterne_id,
                                'location_dest_id':  lot.product_id.property_stock_inventory.id,
                                #surcharge                      
                                'di_poin': abs(poin),            
                                #fin surcharge                        
                                'move_line_ids': [(0, 0, {
                                    'product_id': lot.product_id.id,
                                    'lot_id': lot.id,
                                    'product_uom_qty': 0,  # bypass reservation here
                                    'product_uom_id': lot.product_uom_id.id,
                                    'qty_done': 1.0,                                                                
                                    'location_id': locationinterne_id,
                                    'location_dest_id':lot.product_id.property_stock_inventory.id,                               
                                    #surcharge                            
                                    'di_poin': abs(poin),     
#                                     'di_perte': True           
                                    #fin surcharge
                                })]
                            }
                        self.env['stock.move'].create(vals)
                    elif poin < 0.0:
                        qtediff = qtediff + 1.0
                        vals = {
                                'name': "Clôture lot",
                                'product_id': lot.product_id.id,
                                'product_uom': lot.product_uom_id.id,
                                'product_uom_qty': 0.0,
                                'date': datetime.now(),
                                'company_id': self.env.user.company_id.id,                            
                                'state': 'done',                            
                                'location_id': lot.product_id.property_stock_inventory.id,
                                'location_dest_id': locationinterne_id,
                                #surcharge                      
                                'di_poin': abs(poin),            
                                #fin surcharge                        
                                'move_line_ids': [(0, 0, {
                                    'product_id': lot.product_id.id,
                                    'lot_id': lot.id,
                                    'product_uom_qty': 0,  # bypass reservation here
                                    'product_uom_id': lot.product_uom_id.id,
                                    'qty_done': 1.0,                                                                
                                    'location_id':lot.product_id.property_stock_inventory.id,
                                    'location_dest_id': locationinterne_id,                                
                                    #surcharge                            
                                    'di_poin': abs(poin),     
#                                     'di_perte': True           
                                    #fin surcharge
                                })]
                            }
                        self.env['stock.move'].create(vals)
                    
                    if poib > 0.0:
                        qtediff = qtediff - 1.0
                        vals = {
                                'name': "Clôture lot",
                                'product_id': lot.product_id.id,
                                'product_uom': lot.product_uom_id.id,
                                'product_uom_qty': 0.0,
                                'date': datetime.now(),
                                'company_id': self.env.user.company_id.id,                            
                                'state': 'done',                            
                                'location_id':  locationinterne_id,
                                'location_dest_id':  lot.product_id.property_stock_inventory.id,
                                #surcharge                      
                                'di_poib': abs(poib),            
                                #fin surcharge                        
                                'move_line_ids': [(0, 0, {
                                    'product_id': lot.product_id.id,
                                    'lot_id': lot.id,
                                    'product_uom_qty': 0,  # bypass reservation here
                                    'product_uom_id': lot.product_uom_id.id,
                                    'qty_done': 1.0,                                                                
                                    'location_id': locationinterne_id,
                                    'location_dest_id':lot.product_id.property_stock_inventory.id,                               
                                    #surcharge                            
                                    'di_poib': abs(poib),     
#                                     'di_perte': True           
                                    #fin surcharge
                                })]
                            }
                        self.env['stock.move'].create(vals)
                    elif poib < 0.0:
                        qtediff = qtediff + 1.0
                        vals = {
                                'name': "Clôture lot",
                                'product_id': lot.product_id.id,
                                'product_uom': lot.product_uom_id.id,
                                'product_uom_qty': 0.0,
                                'date': datetime.now(),
                                'company_id': self.env.user.company_id.id,                            
                                'state': 'done',                            
                                'location_id': lot.product_id.property_stock_inventory.id,
                                'location_dest_id': locationinterne_id,
                                #surcharge                      
                                'di_poib': abs(poib),            
                                #fin surcharge                        
                                'move_line_ids': [(0, 0, {
                                    'product_id': lot.product_id.id,
                                    'lot_id': lot.id,
                                    'product_uom_qty': 0,  # bypass reservation here
                                    'product_uom_id': lot.product_uom_id.id,
                                    'qty_done': 1.0,                                                                
                                    'location_id':lot.product_id.property_stock_inventory.id,
                                    'location_dest_id': locationinterne_id,                                
                                    #surcharge                            
                                    'di_poib': abs(poib),     
#                                     'di_perte': True           
                                    #fin surcharge
                                })]
                            }
                        self.env['stock.move'].create(vals)
                    
                    if qtediff != 0.0:
                        if qtediff > 0.0:
                            vals = {
                                    'name': "Clôture lot",
                                    'product_id': lot.product_id.id,
                                    'product_uom': lot.product_uom_id.id,
                                    'product_uom_qty': 0.0,
                                    'date': datetime.now(),
                                    'company_id': self.env.user.company_id.id,                            
                                    'state': 'done',                            
                                    'location_id':  locationinterne_id,
                                    'location_dest_id':  lot.product_id.property_stock_inventory.id,                                                                                      
                                    'move_line_ids': [(0, 0, {
                                        'product_id': lot.product_id.id,
                                        'lot_id': lot.id,
                                        'product_uom_qty': 0,  # bypass reservation here
                                        'product_uom_id': lot.product_uom_id.id,
                                        'qty_done': abs(qtediff),                                                                
                                        'location_id': locationinterne_id,
                                        'location_dest_id':lot.product_id.property_stock_inventory.id,                               
                                        #surcharge                                                                
#                                         'di_perte': True           
                                        #fin surcharge
                                    })]
                                }
                            self.env['stock.move'].create(vals)
                            
                            
                        elif qtediff < 0.0 :
                            vals = {
                                    'name': "Clôture lot",
                                    'product_id': lot.product_id.id,
                                    'product_uom': lot.product_uom_id.id,
                                    'product_uom_qty': 0.0,
                                    'date': datetime.now(),
                                    'company_id': self.env.user.company_id.id,                            
                                    'state': 'done',                            
                                    'location_id':  lot.product_id.property_stock_inventory.id,
                                    'location_dest_id': locationinterne_id ,                                                                                      
                                    'move_line_ids': [(0, 0, {
                                        'product_id': lot.product_id.id,
                                        'lot_id': lot.id,
                                        'product_uom_qty': 0,  # bypass reservation here
                                        'product_uom_id': lot.product_uom_id.id,
                                        'qty_done': abs(qtediff),                                                                
                                        'location_id': lot.product_id.property_stock_inventory.id,
                                        'location_dest_id': locationinterne_id,                               
                                        #surcharge                                                                
#                                         'di_perte': True           
                                        #fin surcharge
                                    })]
                                }
                        
                            self.env['stock.move'].create(vals)
                                                                    
                    lot.update({'di_fini':True,}) 
            
        self.env['stock.quant']._unlink_zero_quants()
        return lots                    
