# -*- coding: utf-8 -*-
from odoo import api, fields, models
from datetime import timedelta, datetime
import io
# import os
import base64
# from ..models import di_outils
# from pip._internal import download
from odoo.tools import pycompat

class DiRegulArtLots(models.TransientModel):
    _name = "di.regul.art.lot.wiz"
    _description = "Wizard de régul des stock par article et lot"
    
    date_regul = fields.Datetime("Date de régul.", default=datetime.now())
        
    di_product_id = fields.Many2one('product.product',string="Article")
    di_lot_id  =   fields.Many2one('stock.production.lot', string="Lot")
    
    
    di_qte_std = fields.Float(string='Quantité en unité de mesure')
    di_nb_pieces = fields.Integer(string='Nb pièces')
    di_nb_colis = fields.Integer(string='Nb colis' )
    di_nb_palette = fields.Float(string='Nb palettes' )
    di_poin = fields.Float(string='Poids net' )
    di_tare_un = fields.Float(string='Tare unitaire' )
    di_poib = fields.Float(string='Poids brut' )        
    
    di_qte_std_theo = fields.Float(string='Quantité théorique en unité de mesure ', readonly=True, store=True, compute="_compute_qte_theo")
    di_nb_pieces_theo = fields.Integer(string='Nb pièces théorique', readonly=True, store=True, compute="_compute_qte_theo")
    di_nb_colis_theo = fields.Integer(string='Nb colis théorique' , readonly=True, store=True, compute="_compute_qte_theo")
    di_nb_palette_theo = fields.Float(string='Nb palettes théorique' , readonly=True, store=True, compute="_compute_qte_theo")
    di_poin_theo = fields.Float(string='Poids net théorique' , readonly=True, store=True, compute="_compute_qte_theo")
    di_poib_theo = fields.Float(string='Poids brut théorique' , readonly=True, store=True, compute="_compute_qte_theo")   
    
    
    @api.depends('di_product_id','di_lot_id')
    def _compute_qte_theo(self):
        if self.di_product_id and self.di_lot_id:
            (nbcol,nbpal,nbpiece,poin,qte,poib)= self.env['stock.move.line'].di_qte_spe_en_stock(self.di_product_id,False,self.di_lot_id)
            self.di_qte_std_theo = qte
            self.di_nb_pieces_theo = nbpiece
            self.di_nb_colis_theo = nbcol
            self.di_nb_palette_theo = nbpal
            self.di_poin_theo = poin
            self.di_poib_theo = poib  

        else:
            self.di_qte_std_theo = 0.0
            self.di_nb_pieces_theo = 0.0
            self.di_nb_colis_theo = 0.0
            self.di_nb_palette_theo = 0.0
            self.di_poin_theo = 0.0
            self.di_poib_theo = 0.0  
        self.di_qte_std = self.di_qte_std_theo
        self.di_nb_pieces = self.di_nb_pieces_theo
        self.di_nb_colis = self.di_nb_colis_theo
        self.di_nb_palette = self.di_nb_palette_theo
        self.di_poin = self.di_poin_theo
        self.di_poib = self.di_poib_theo  
                 
    
    
#     @api.onchange('di_qte_std_theo','di_nb_pieces_theo','di_nb_colis_theo','di_nb_palette_theo','di_poin_theo','di_poib_theo')
#     def _init_qtes_reelles(self):                      
#         self.di_qte_std = di_qte_std_theo
#         self.di_nb_pieces = di_nb_pieces_theo
#         self.di_nb_colis = di_nb_colis_theo
#         self.di_nb_palette = di_nb_palette_theo
#         self.di_poin = di_poin_theo
#         self.di_poib = di_poib_theo

    @api.onchange('di_poib','di_tare_un')
    def di_onchange_poib_tare(self):
        self.di_poin = self.di_poib - (self.di_tare_un*self.di_nb_colis)
        
  
    @api.multi
    def valider_regul(self):
        self.ensure_one()  
       
        nbcol = self.di_nb_colis - self.di_nb_colis_theo
        nbpal=self.di_nb_palette - self.di_nb_palette_theo
        nbpiece = self.di_nb_pieces - self.di_nb_pieces_theo
        poin =self.di_poin - self.di_poin_theo
        qtediff =self.di_qte_std - self.di_qte_std_theo
        poib=self.di_poib - self.di_poib_theo
        
#         qtediff = 0.0                
        if nbcol != 0.0 or nbpal != 0.0 or nbpiece != 0.0 or poin != 0.0 or poib != 0.0 or qtediff != 0.0:                
            locationinterne_id = self.env['stock.picking.type'].search([('code','=','incoming')], limit=1).default_location_dest_id.id
            if nbcol < 0.0:
                qtediff = qtediff + 1.0
                vals = {
                        'name': "Régul. article lot",
                        'product_id': self.di_product_id.id,
                        'product_uom': self.di_product_id.uom_id.id,
                        'product_uom_qty': 0.0,
                        'date': self.date_regul,
                        'company_id': self.env.user.company_id.id,                            
                        'state': 'done',                            
                        'location_id':  locationinterne_id,
                        'location_dest_id':  self.di_product_id.property_stock_inventory.id,
                        #surcharge                      
                        'di_nb_colis': abs(nbcol),            
                        #fin surcharge                        
                        'move_line_ids': [(0, 0, {
                            'product_id': self.di_product_id.id,
                            'lot_id': self.di_lot_id.id,
                            'product_uom_qty': 0,  # bypass reservation here
                            'product_uom_id': self.di_product_id.uom_id.id,
                            'qty_done': 1.0,                                                                
                            'location_id': locationinterne_id,
                            'location_dest_id':self.di_product_id.property_stock_inventory.id,                               
                            #surcharge                            
                            'di_nb_colis': abs(nbcol),     
#                             'di_perte': True           
                            #fin surcharge
                        })]
                    }
            elif nbcol > 0.0:
                qtediff = qtediff - 1.0
                vals = {
                        'name': "Régul. article lot",
                        'product_id': self.di_product_id.id,
                        'product_uom': self.di_product_id.uom_id.id,
                        'product_uom_qty': 0.0,
                        'date': self.date_regul,
                        'company_id': self.env.user.company_id.id,                            
                        'state': 'done',                            
                        'location_id': self.di_product_id.property_stock_inventory.id,
                        'location_dest_id': locationinterne_id,
                        #surcharge                      
                        'di_nb_colis': abs(nbcol),            
                        #fin surcharge                        
                        'move_line_ids': [(0, 0, {
                            'product_id': self.di_product_id.id,
                            'lot_id': self.di_lot_id.id,
                            'product_uom_qty': 0,  # bypass reservation here
                            'product_uom_id': self.di_product_id.uom_id.id,
                            'qty_done': 1.0,                                                                
                            'location_id':self.di_product_id.property_stock_inventory.id,
                            'location_dest_id': locationinterne_id,                                
                            #surcharge                            
                            'di_nb_colis': abs(nbcol),     
#                             'di_perte': True           
                            #fin surcharge
                        })]
                    }
            self.env['stock.move'].create(vals)
            
            if nbpal < 0.0:
                qtediff = qtediff + 1.0
                vals = {
                        'name': "Régul. article lot",
                        'product_id': self.di_product_id.id,
                        'product_uom': self.di_product_id.uom_id.id,
                        'product_uom_qty': 0.0,
                        'date': self.date_regul,
                        'company_id': self.env.user.company_id.id,                            
                        'state': 'done',                            
                        'location_id':  locationinterne_id,
                        'location_dest_id':  self.di_product_id.property_stock_inventory.id,
                        #surcharge                      
                        'di_nb_palette': abs(nbpal),            
                        #fin surcharge                        
                        'move_line_ids': [(0, 0, {
                            'product_id': self.di_product_id.id,
                            'lot_id': self.di_lot_id.id,
                            'product_uom_qty': 0,  # bypass reservation here
                            'product_uom_id': self.di_product_id.uom_id.id,
                            'qty_done': 1.0,                                                                
                            'location_id': locationinterne_id,
                            'location_dest_id':self.di_product_id.property_stock_inventory.id,                               
                            #surcharge                            
                            'di_nb_palette': abs(nbpal),     
#                             'di_perte': True           
                            #fin surcharge
                        })]
                    }
            elif nbpal > 0.0:
                qtediff = qtediff - 1.0
                vals = {
                        'name': "Régul. article lot",
                        'product_id': self.di_product_id.id,
                        'product_uom': self.di_product_id.uom_id.id,
                        'product_uom_qty': 0.0,
                        'date': self.date_regul,
                        'company_id': self.env.user.company_id.id,                            
                        'state': 'done',                            
                        'location_id': self.di_product_id.property_stock_inventory.id,
                        'location_dest_id': locationinterne_id,
                        #surcharge                      
                        'di_nb_palette': abs(nbpal),            
                        #fin surcharge                        
                        'move_line_ids': [(0, 0, {
                            'product_id': self.di_product_id.id,
                            'lot_id': self.di_lot_id.id,
                            'product_uom_qty': 0,  # bypass reservation here
                            'product_uom_id': self.di_product_id.uom_id.id,
                            'qty_done': 1.0,                                                                
                            'location_id':self.di_product_id.property_stock_inventory.id,
                            'location_dest_id': locationinterne_id,                                
                            #surcharge                            
                            'di_nb_palette': abs(nbpal),     
#                             'di_perte': True           
                            #fin surcharge
                        })]
                    }
            self.env['stock.move'].create(vals)
            
            if nbpiece < 0.0:
                qtediff = qtediff + 1.0
                vals = {
                        'name': "Régul. article lot",
                        'product_id': self.di_product_id.id,
                        'product_uom': self.di_product_id.uom_id.id,
                        'product_uom_qty': 0.0,
                        'date': self.date_regul,
                        'company_id': self.env.user.company_id.id,                            
                        'state': 'done',                            
                        'location_id':  locationinterne_id,
                        'location_dest_id':  self.di_product_id.property_stock_inventory.id,
                        #surcharge                      
                        'di_nb_pieces': abs(nbpiece),            
                        #fin surcharge                        
                        'move_line_ids': [(0, 0, {
                            'product_id': self.di_product_id.id,
                            'lot_id': self.di_lot_id.id,
                            'product_uom_qty': 0,  # bypass reservation here
                            'product_uom_id': self.di_product_id.uom_id.id,
                            'qty_done': 1.0,                                                                
                            'location_id': locationinterne_id,
                            'location_dest_id':self.di_product_id.property_stock_inventory.id,                               
                            #surcharge                            
                            'di_nb_pieces': abs(nbpiece),     
#                             'di_perte': True           
                            #fin surcharge
                        })]
                    }
            elif nbpiece > 0.0:
                qtediff = qtediff - 1.0
                vals = {
                        'name': "Régul. article lot",
                        'product_id': self.di_product_id.id,
                        'product_uom': self.di_product_id.uom_id.id,
                        'product_uom_qty': 0.0,
                        'date': self.date_regul,
                        'company_id': self.env.user.company_id.id,                            
                        'state': 'done',                            
                        'location_id': self.di_product_id.property_stock_inventory.id,
                        'location_dest_id': locationinterne_id,
                        #surcharge                      
                        'di_nb_pieces': abs(nbpiece),            
                        #fin surcharge                        
                        'move_line_ids': [(0, 0, {
                            'product_id': self.di_product_id.id,
                            'lot_id': self.di_lot_id.id,
                            'product_uom_qty': 0,  # bypass reservation here
                            'product_uom_id': self.di_product_id.uom_id.id,
                            'qty_done': 1.0,                                                                
                            'location_id':self.di_product_id.property_stock_inventory.id,
                            'location_dest_id': locationinterne_id,                                
                            #surcharge                            
                            'di_nb_pieces': abs(nbpiece),     
#                             'di_perte': True           
                            #fin surcharge
                        })]
                    }
            self.env['stock.move'].create(vals)
            
            if poin < 0.0:
                qtediff = qtediff + 1.0
                vals = {
                        'name': "Régul. article lot",
                        'product_id': self.di_product_id.id,
                        'product_uom': self.di_product_id.uom_id.id,
                        'product_uom_qty': 0.0,
                        'date': self.date_regul,
                        'company_id': self.env.user.company_id.id,                            
                        'state': 'done',                            
                        'location_id':  locationinterne_id,
                        'location_dest_id':  self.di_product_id.property_stock_inventory.id,
                        #surcharge                      
                        'di_poin': abs(poin),            
                        #fin surcharge                        
                        'move_line_ids': [(0, 0, {
                            'product_id': self.di_product_id.id,
                            'lot_id': self.di_lot_id.id,
                            'product_uom_qty': 0,  # bypass reservation here
                            'product_uom_id': self.di_product_id.uom_id.id,
                            'qty_done': 1.0,                                                                
                            'location_id': locationinterne_id,
                            'location_dest_id':self.di_product_id.property_stock_inventory.id,                               
                            #surcharge                            
                            'di_poin': abs(poin),     
#                             'di_perte': True           
                            #fin surcharge
                        })]
                    }
            elif poin > 0.0:
                qtediff = qtediff - 1.0
                vals = {
                        'name': "Régul. article lot",
                        'product_id': self.di_product_id.id,
                        'product_uom': self.di_product_id.uom_id.id,
                        'product_uom_qty': 0.0,
                        'date': self.date_regul,
                        'company_id': self.env.user.company_id.id,                            
                        'state': 'done',                            
                        'location_id': self.di_product_id.property_stock_inventory.id,
                        'location_dest_id': locationinterne_id,
                        #surcharge                      
                        'di_poin': abs(poin),            
                        #fin surcharge                        
                        'move_line_ids': [(0, 0, {
                            'product_id': self.di_product_id.id,
                            'lot_id': self.di_lot_id.id,
                            'product_uom_qty': 0,  # bypass reservation here
                            'product_uom_id': self.di_product_id.uom_id.id,
                            'qty_done': 1.0,                                                                
                            'location_id':self.di_product_id.property_stock_inventory.id,
                            'location_dest_id': locationinterne_id,                                
                            #surcharge                            
                            'di_poin': abs(poin),     
#                             'di_perte': True           
                            #fin surcharge
                        })]
                    }
            self.env['stock.move'].create(vals)
            
            if poib < 0.0:
                qtediff = qtediff + 1.0
                vals = {
                        'name': "Régul. article lot",
                        'product_id': self.di_product_id.id,
                        'product_uom': self.di_product_id.uom_id.id,
                        'product_uom_qty': 0.0,
                        'date': self.date_regul,
                        'company_id': self.env.user.company_id.id,                            
                        'state': 'done',                            
                        'location_id':  locationinterne_id,
                        'location_dest_id':  self.di_product_id.property_stock_inventory.id,
                        #surcharge                      
                        'di_poib': abs(poib),            
                        #fin surcharge                        
                        'move_line_ids': [(0, 0, {
                            'product_id': self.di_product_id.id,
                            'lot_id': self.di_lot_id.id,
                            'product_uom_qty': 0,  # bypass reservation here
                            'product_uom_id': self.di_product_id.uom_id.id,
                            'qty_done': 1.0,                                                                
                            'location_id': locationinterne_id,
                            'location_dest_id':self.di_product_id.property_stock_inventory.id,                               
                            #surcharge                            
                            'di_poib': abs(poib),     
#                             'di_perte': True           
                            #fin surcharge
                        })]
                    }
            elif poib > 0.0:
                qtediff = qtediff - 1.0
                vals = {
                        'name': "Régul. article lot",
                        'product_id': self.di_product_id.id,
                        'product_uom': self.di_product_id.uom_id.id,
                        'product_uom_qty': 0.0,
                        'date': self.date_regul,
                        'company_id': self.env.user.company_id.id,                            
                        'state': 'done',                            
                        'location_id': self.di_product_id.property_stock_inventory.id,
                        'location_dest_id': locationinterne_id,
                        #surcharge                      
                        'di_poib': abs(poib),            
                        #fin surcharge                        
                        'move_line_ids': [(0, 0, {
                            'product_id': self.di_product_id.id,
                            'lot_id': self.di_lot_id.id,
                            'product_uom_qty': 0,  # bypass reservation here
                            'product_uom_id': self.di_product_id.uom_id.id,
                            'qty_done': 1.0,                                                                
                            'location_id':self.di_product_id.property_stock_inventory.id,
                            'location_dest_id': locationinterne_id,                                
                            #surcharge                            
                            'di_poib': abs(poib),     
#                             'di_perte': True           
                            #fin surcharge
                        })]
                    }
            self.env['stock.move'].create(vals)
            
            if qtediff != 0.0:
                if qtediff < 0.0:
                    vals = {
                            'name': "Régul. article lot",
                            'product_id': self.di_product_id.id,
                            'product_uom': self.di_product_id.uom_id.id,
                            'product_uom_qty': 0.0,
                            'date': self.date_regul,
                            'company_id': self.env.user.company_id.id,                            
                            'state': 'done',                            
                            'location_id':  locationinterne_id,
                            'location_dest_id':  self.di_product_id.property_stock_inventory.id,                                                                                      
                            'move_line_ids': [(0, 0, {
                                'product_id': self.di_product_id.id,
                                'lot_id': self.di_lot_id.id,
                                'product_uom_qty': 0,  # bypass reservation here
                                'product_uom_id': self.di_product_id.uom_id.id,
                                'qty_done': abs(qtediff),                                                                
                                'location_id': locationinterne_id,
                                'location_dest_id':self.di_product_id.property_stock_inventory.id,                               
                                #surcharge                                                                
#                                 'di_perte': True           
                                #fin surcharge
                            })]
                        }
                    
                    
                elif qtediff > 0.0 :
                    vals = {
                            'name': "Régul. article lot",
                            'product_id': self.di_product_id.id,
                            'product_uom': self.di_product_id.uom_id.id,
                            'product_uom_qty': 0.0,
                            'date': self.date_regul,
                            'company_id': self.env.user.company_id.id,                            
                            'state': 'done',                            
                            'location_id':  self.di_product_id.property_stock_inventory.id,
                            'location_dest_id': locationinterne_id ,                                                                                      
                            'move_line_ids': [(0, 0, {
                                'product_id': self.di_product_id.id,
                                'lot_id': self.di_lot_id.id,
                                'product_uom_qty': 0,  # bypass reservation here
                                'product_uom_id': self.di_product_id.uom_id.id,
                                'qty_done': abs(qtediff),                                                                
                                'location_id': self.di_product_id.property_stock_inventory.id,
                                'location_dest_id': locationinterne_id,                               
                                #surcharge                                                                
#                                 'di_perte': True           
                                #fin surcharge
                            })]
                        }
                
                self.env['stock.move'].create(vals)
                
                
                
        def ref(module, xml_id):
            proxy = self.env['ir.model.data']
            return proxy.get_object_reference(module, xml_id)        
                
         
        model, view_id = ref('difodoo_ventes', 'di_regul_art_lot_msgfin')
        
      
        views = [
            (view_id, 'form'),     
        ]                
                
#         view_id = self.env.ref('difodoo_ventes.di_regul_art_lot_msgfin')[0]                                                                                        
        return {
        'name':"Traitement terminé",#Name You want to display on wizard
        'view_mode': 'form',        
        'view_type': 'form',
        'res_model': 'di.regul.art.lot.wiz',
        'type': 'ir.actions.act_window',
        'target': 'new',
        'view_id': False,
        'views':views
    }    
        
        
    @api.multi
    def continuer_regul(self):
        self.ensure_one()  
#         view_id = self.env.ref('difodoo_ventes.di_regul_art_lot_wiz_form')
        def ref(module, xml_id):
            proxy = self.env['ir.model.data']
            return proxy.get_object_reference(module, xml_id)        
                
         
        model, view_id = ref('difodoo_ventes', 'di_regul_art_lot_wiz_form')
        
      
        views = [
            (view_id, 'form'),     
        ]                                                                                                         
        return {            
            'view_mode': 'form',        
            'view_type': 'form',
            'res_model': 'di.regul.art.lot.wiz',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'view_id': False,
            'views':views
    }               
        
    
