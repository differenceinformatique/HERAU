# -*- coding: utf-8 -*-
from datetime import datetime,timedelta

from odoo import models, fields, api, _
from odoo.tools import float_utils
from math import ceil

class Inventory(models.Model):
    _inherit = "stock.inventory"
    
    def action_reset_product_qty(self):
        ret=super(Inventory, self).action_reset_product_qty()
        self.mapped('line_ids').write({'di_nb_colis': 0})
        self.mapped('line_ids').write({'di_nb_pieces': 0}) 
        self.mapped('line_ids').write({'di_nb_palette': 0}) 
        self.mapped('line_ids').write({'di_poin': 0})                                 
        return ret
    
    def _get_inventory_lines_values(self):
        # copie standard
        # je n'ai pas réussi à surcharger proprement donc j'ai repris tout le standard
        # TDE CLEANME: is sql really necessary ? I don't think so
        locations = self.env['stock.location'].search([('id', 'child_of', [self.location_id.id])])
        domain = ' location_id in %s'
        args = (tuple(locations.ids),)

        vals = []
        Product = self.env['product.product']
        # Empty recordset of products available in stock_quants
        quant_products = self.env['product.product']
        # Empty recordset of products to filter
        products_to_filter = self.env['product.product']

        # case 0: Filter on company
        if self.company_id:
            domain += ' AND company_id = %s'
            args += (self.company_id.id,)
        
        #case 1: Filter on One owner only or One product for a specific owner
        if self.partner_id:
            domain += ' AND owner_id = %s'
            args += (self.partner_id.id,)
        #case 2: Filter on One Lot/Serial Number
        if self.lot_id:
            domain += ' AND lot_id = %s'
            args += (self.lot_id.id,)
        #case 3: Filter on One product
        if self.product_id:
            domain += ' AND product_id = %s'
            args += (self.product_id.id,)
            products_to_filter |= self.product_id
        #case 4: Filter on A Pack
        if self.package_id:
            domain += ' AND package_id = %s'
            args += (self.package_id.id,)
        #case 5: Filter on One product category + Exahausted Products
        if self.category_id:
            categ_products = Product.search([('categ_id', '=', self.category_id.id)])
            domain += ' AND product_id = ANY (%s)'
            args += (categ_products.ids,)
            products_to_filter |= categ_products

        self.env.cr.execute("""SELECT product_id, sum(quantity) as product_qty, location_id, lot_id as prod_lot_id, package_id, owner_id as partner_id
            FROM stock_quant
            WHERE %s
            GROUP BY product_id, location_id, lot_id, package_id, partner_id """ % domain, args)

        for product_data in self.env.cr.dictfetchall():
            # replace the None the dictionary by False, because falsy values are tested later on
            for void_field in [item[0] for item in product_data.items() if item[1] is None]:
                product_data[void_field] = False
            product_data['theoretical_qty'] = product_data['product_qty']
            if product_data['product_id']:
                product_data['product_uom_id'] = Product.browse(product_data['product_id']).uom_id.id
                quant_products |= Product.browse(product_data['product_id'])
            #surcharge pour initialiser les quantités spé 
            nbcol=0.0
            nbpal=0.0
            nbpiece=0.0
            poids=0.0   
            lot = self.env['stock.production.lot'].browse(product_data['prod_lot_id'])    
            article = self.env['product.product'].browse(product_data['product_id']) 
            (nbcol,nbpal,nbpiece,poids,qte_std) = self.env['stock.move.line'].di_qte_spe_en_stock(article,self.date.date(),lot)#        
            product_data['di_nb_colis']=nbcol
            product_data['di_nb_pieces']= nbpiece 
            product_data['di_nb_palette']=  nbpal
            product_data['di_poin']=  poids 
            product_data['di_nb_colis_theo']=nbcol
            product_data['di_nb_pieces_theo']= nbpiece 
            product_data['di_nb_palette_theo']=  nbpal
            product_data['di_poin_theo']=  poids 
            #fin surcharge
            vals.append(product_data)
        if self.exhausted:
            exhausted_vals = self._get_exhausted_inventory_line(products_to_filter, quant_products)
            vals.extend(exhausted_vals)
                       
        return vals
    
class InventoryLine(models.Model):
    _inherit = "stock.inventory.line"         
                 
    di_nb_pieces = fields.Integer(string='Nb pièces', store=True)#, compute='_di_compute_qte_spe')
    di_nb_colis = fields.Integer(string='Nb colis' , store=True)#, compute='_di_compute_qte_spe')
    di_nb_palette = fields.Float(string='Nb palettes' , store=True)#, compute='_di_compute_qte_spe')
    di_poin = fields.Float(string='Poids' , store=True)#, compute='_di_compute_qte_spe')        
    
    di_nb_pieces_theo = fields.Integer(string='Nb pièces théorique', store=True, compute='_compute_theoretical_qty')
    di_nb_colis_theo = fields.Integer(string='Nb colis théorique' , store=True, compute='_compute_theoretical_qty')
    di_nb_palette_theo = fields.Float(string='Nb palettes théorique' , store=True, compute='_compute_theoretical_qty')
    di_poin_theo = fields.Float(string='Poids théorique' , store=True, compute='_compute_theoretical_qty')   
    
    di_ecart_qte= fields.Float(string='Ecart quantité' , store=True, compute='_compute_ecart')       
    
    @api.multi
    @api.depends('product_qty', 'theoretical_qty')
    def _compute_ecart(self):    
        for sil in self:                
            sil.di_ecart_qte = sil.product_qty - sil.theoretical_qty                                        
         
        
    @api.one # SC je garde api.one car on surcharge une fonction qui est en api.one
    @api.depends('location_id', 'product_id', 'package_id', 'product_uom_id', 'company_id', 'prod_lot_id', 'partner_id')
    def _compute_theoretical_qty(self):                     
        super(InventoryLine, self)._compute_theoretical_qty()
        qte=0.0
        nbcol = 0.0
        nbpal = 0.0
        nbpiece = 0.0
        poids = 0.0
        if self.product_id and self.inventory_id.date:
            (nbcol,nbpal,nbpiece,poids,qte_std) = self.env['stock.move.line'].di_qte_spe_en_stock(self.product_id,self.inventory_id.date.date(),self.prod_lot_id)#            
        self.di_nb_colis_theo = nbcol 
        self.di_nb_palette_theo = nbpal
        self.di_poin_theo = poids
        self.di_nb_pieces_theo = nbpiece                          
                                                                
                                                                
                                                                
    @api.onchange('product_id', 'location_id', 'product_uom_id', 'prod_lot_id', 'partner_id', 'package_id')
    def di_onchange_quantity_context(self):
#         super(InventoryLine, self).onchange_quantity_context()
         
        if self.product_id and self.location_id and self.product_id.uom_id.category_id == self.product_uom_id.category_id:  # TDE FIXME: last part added because crash
            self._compute_theoretical_qty()                        
            self.di_nb_colis = self.di_nb_colis_theo
            self.di_nb_palette = self.di_nb_palette_theo
            self.di_nb_pieces = self.di_nb_pieces_theo
            self.di_poin = self.di_poin_theo
            
            
            
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
                'product_uom_qty': 0,  # bypass reservation here
                'product_uom_id': self.product_uom_id.id,
                'qty_done': 1.0,
                'package_id': out and self.package_id.id or False,
                'result_package_id': (not out) and self.package_id.id or False,
                'location_id': location_id,
                'location_dest_id': location_dest_id,
                'owner_id': self.partner_id.id,
                #surcharge                            
                'di_nb_colis': qty                
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
                'product_uom_qty': 0,  # bypass reservation here
                'product_uom_id': self.product_uom_id.id,
                'qty_done': 1.0,
                'package_id': out and self.package_id.id or False,
                'result_package_id': (not out) and self.package_id.id or False,
                'location_id': location_id,
                'location_dest_id': location_dest_id,
                'owner_id': self.partner_id.id,
                #surcharge                            
                'di_nb_pieces': qty                
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
                'product_uom_qty': 0,  # bypass reservation here
                'product_uom_id': self.product_uom_id.id,
                'qty_done': 1.0,
                'package_id': out and self.package_id.id or False,
                'result_package_id': (not out) and self.package_id.id or False,
                'location_id': location_id,
                'location_dest_id': location_dest_id,
                'owner_id': self.partner_id.id,
                #surcharge                            
                'di_poin': qty                
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
                'product_uom_qty': 0,  # bypass reservation here
                'product_uom_id': self.product_uom_id.id,
                'qty_done': 1.0,
                'package_id': out and self.package_id.id or False,
                'result_package_id': (not out) and self.package_id.id or False,
                'location_id': location_id,
                'location_dest_id': location_dest_id,
                'owner_id': self.partner_id.id,
                #surcharge                            
                'di_nb_palette': qty                
                #fin surcharge
            })]
        }

    def _generate_moves(self):
        # copie standard
        #je dois surcharger en copiant le standard
#         moves = self.env['stock.move'] # v11
        vals_list = [] # v12
        for line in self:
            if float_utils.float_compare(line.theoretical_qty, line.product_qty, precision_rounding=line.product_id.uom_id.rounding) == 0 \
            and float_utils.float_compare(line.di_nb_palette_theo, line.di_nb_palette, precision_rounding=line.product_id.uom_id.rounding) == 0 \
            and float_utils.float_compare(line.di_nb_colis_theo, line.di_nb_colis, precision_rounding=line.product_id.uom_id.rounding) == 0 \
            and float_utils.float_compare(line.di_nb_pieces_theo, line.di_nb_pieces, precision_rounding=line.product_id.uom_id.rounding) == 0 \
            and float_utils.float_compare(line.di_poin_theo, line.di_poin, precision_rounding=line.product_id.uom_id.rounding) == 0 :                                    
                continue
            diff = line.theoretical_qty - line.product_qty
            di_diff_pal = line.di_nb_palette_theo - line.di_nb_palette
            di_diff_col = line.di_nb_colis_theo - line.di_nb_colis
            di_diff_piece = line.di_nb_pieces_theo - line.di_nb_pieces
            di_diff_poids = line.di_poin_theo - line.di_poin
                        
            
            if di_diff_pal < 0:  # found more than expected
                diff = diff + 1 # obligé de mettre qty_done = 1 pour que le move soit créé, je rétabli la quantité
                vals = line._di_get_move_values_pal(abs(di_diff_pal), line.product_id.property_stock_inventory.id, line.location_id.id, False)
            else:
                diff = diff - 1
                vals = line._di_get_move_values_pal(abs(di_diff_pal), line.location_id.id, line.product_id.property_stock_inventory.id, True)
#             moves |= self.env['stock.move'].create(vals)# v11
            vals_list.append(vals) #v12
            
            if di_diff_col < 0:  # found more than expected
                diff = diff + 1
                vals = line._di_get_move_values_col(abs(di_diff_col), line.product_id.property_stock_inventory.id, line.location_id.id, False)
            else:
                diff = diff - 1
                vals = line._di_get_move_values_col(abs(di_diff_col), line.location_id.id, line.product_id.property_stock_inventory.id, True)
#             moves |= self.env['stock.move'].create(vals)# v11
            vals_list.append(vals)#v12
            
            if di_diff_piece < 0:  # found more than expected
                diff = diff + 1
                vals = line._di_get_move_values_piece(abs(di_diff_piece), line.product_id.property_stock_inventory.id, line.location_id.id, False)
            else:
                diff = diff - 1
                vals = line._di_get_move_values_piece(abs(di_diff_piece), line.location_id.id, line.product_id.property_stock_inventory.id, True)
#             moves |= self.env['stock.move'].create(vals)# v11
            vals_list.append(vals)#v12
            
            if di_diff_poids < 0:  # found more than expected
                diff = diff + 1
                vals = line._di_get_move_values_poids(abs(di_diff_poids), line.product_id.property_stock_inventory.id, line.location_id.id, False)
            else:
                diff = diff - 1
                vals = line._di_get_move_values_poids(abs(di_diff_poids), line.location_id.id, line.product_id.property_stock_inventory.id, True)
#             moves |= self.env['stock.move'].create(vals)# v11
            vals_list.append(vals)#v12
            
            if diff < 0:  # found more than expected
                vals = line._get_move_values(abs(diff), line.product_id.property_stock_inventory.id, line.location_id.id, False)
            else:
                vals = line._get_move_values(abs(diff), line.location_id.id, line.product_id.property_stock_inventory.id, True)
#             moves |= self.env['stock.move'].create(vals)# v11
            vals_list.append(vals)#v12
                                               
#         return moves # v11
        return self.env['stock.move'].create(vals_list)#v12