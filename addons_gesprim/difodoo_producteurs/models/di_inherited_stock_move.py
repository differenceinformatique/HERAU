# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from math import *
from datetime import  datetime
 
class StockMove(models.Model):
    _inherit = "stock.move"
   
    di_categorie_id = fields.Many2one("di.categorie", string="Catégorie", compute='_di_compute_champs_art_init')    
    di_categorie_di_des = fields.Char(related='di_categorie_id.di_des')  # , store='False')
    
    di_origine_id = fields.Many2one("di.origine", string="Origine", compute='_di_compute_champs_art_init')
    di_origine_di_des = fields.Char(related='di_origine_id.di_des')  # , store='False')
    
    di_marque_id = fields.Many2one("di.marque", string="Marque", compute='_di_compute_champs_art_init')
    di_marque_di_des = fields.Char(related='di_marque_id.di_des')  # , store='False')
    
    di_calibre_id = fields.Many2one("di.calibre", string="Calibre", compute='_di_compute_champs_art_init')
    di_calibre_di_des = fields.Char(related='di_calibre_id.di_des')
    
    di_station_id = fields.Many2one("stock.location", string="Station", compute='_di_compute_champs_art_init')
    di_station_di_des = fields.Char(related='di_station_id.name')  # , store='False')     
     
    @api.multi
    @api.depends('sale_line_id','purchase_line_id')
    def _di_compute_champs_art_init(self): 
        for sm in self:
            if sm.sale_line_id :
                sm.di_categorie_id = sm.sale_line_id.di_categorie_id
                sm.di_origine_id = sm.sale_line_id.di_origine_id
                sm.di_marque_id = sm.sale_line_id.di_marque_id
                sm.di_calibre_id = sm.sale_line_id.di_calibre_id
                sm.di_station_id = sm.sale_line_id.di_station_id 
            elif sm.purchase_line_id:
                sm.di_categorie_id = sm.purchase_line_id.di_categorie_id
                sm.di_origine_id = sm.purchase_line_id.di_origine_id
                sm.di_marque_id = sm.purchase_line_id.di_marque_id
                sm.di_calibre_id = sm.purchase_line_id.di_calibre_id            
     
    @api.multi            
    @api.onchange('product_id')
    def _di_charger_valeur_par_defaut(self):
        super(StockMove, self)._di_charger_valeur_par_defaut()        
        if self.ensure_one():
            if self.picking_partner_id and self.product_id:
                ref = self.env['di.ref.art.tiers'].search([('di_partner_id','=',self.picking_partner_id.id),('di_product_id','=',self.product_id.id)],limit=1)
            else:
                ref = False
            if ref:                        
                self.di_categorie_id = self.product_id.di_categorie_id 
                self.di_origine_id = self.product_id.di_origine_id 
                self.di_marque_id = self.product_id.di_marque_id 
                self.di_calibre_id = self.product_id.di_calibre_id                               
                self.di_station_id = ref.di_station_id 
            else:
                if self.product_id:                                 
                    self.di_categorie_id = self.product_id.di_categorie_id 
                    self.di_origine_id = self.product_id.di_origine_id 
                    self.di_marque_id = self.product_id.di_marque_id 
                    self.di_calibre_id = self.product_id.di_calibre_id 
                    self.di_station_id = self.product_id.di_station_id 

            
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
                    # on attribue par défaut les valeurs de la ligne de commande                                   
                    vals["di_categorie_id"] = Disaleorderline.di_categorie_id.id
                    vals["di_origine_id"] = Disaleorderline.di_origine_id.id
                    vals["di_marque_id"] = Disaleorderline.di_marque_id.id
                    vals["di_calibre_id"] = Disaleorderline.di_calibre_id.id
                    vals["di_station_id"] = Disaleorderline.di_station_id.id
                    if Disaleorderline.di_station_id:
                        vals["location_id"] = Disaleorderline.di_station_id.id
                                                            
        
        if vals.get('purchase_line_id'):    
            purchaseline = self.env['purchase.order.line'].search([('id', '=', vals["purchase_line_id"])], limit=1)            
            if purchaseline.id != False:                
                vals["di_categorie_id"] = purchaseline.di_categorie_id.id
                vals["di_origine_id"] = purchaseline.di_origine_id.id
                vals["di_marque_id"] = purchaseline.di_marque_id.id
                vals["di_calibre_id"] = purchaseline.di_calibre_id.id
                                                                      
        res = super(StockMove, self).create(vals)                                                   

        return res
    
                 
class StockMoveLine(models.Model):
    _inherit = "stock.move.line"
  
    di_lot_prod = fields.Char(string="Lot producteur", store=True)
    di_lot_cli = fields.Char(string="Lot client", store=True)  # certains client veulent un n° de lot particulier pour pouvoir le scanner
    di_ES = fields.Char(string="Entrée ou sortie", store=True, compute="_compute_di_ES")        
    
    def di_get_lot_prod(self,product_id,id_lot):
        lot_prod=''
        move_line = self.env['stock.move.line'].search(['&', ('product_id', '=', product_id), ('lot_id', '=', id_lot), ('move_id.state', '=', 'done'), ('location_dest_id.usage', '=', 'internal'), ('di_lot_prod', '!=', False)],limit=1)            
        if move_line:
            if move_line.di_lot_prod:
                lot_prod = move_line.di_lot_prod
        
        return lot_prod
       

    @api.multi
    @api.depends('move_id.picking_type_id.code')
    def _compute_di_ES(self):   
        for sml in self:
            if sml.move_id.picking_type_id.code == 'incoming':
                sml.di_ES = "entree"
            else:
                sml.di_ES = "sortie"                  
                
            
    @api.model
    def create(self, vals):
        if vals.get('picking_id') :
            if vals['picking_id'] != False:                  
                picking = self.env['stock.picking'].browse(vals['picking_id'])
                if picking.picking_type_id.code == 'incoming':                     
                                       
                    if not vals.get('lot_id'):  # si pas de lot saisi
                        if vals.get('move_id') :  # si on a une commande liée
                            if vals['move_id'] != False:            
                                move = self.env['stock.move'].browse(vals['move_id'])
                                if move.product_id.tracking != 'none':
                                    if move.purchase_line_id.order_id.id != False:
                                        if move.product_id.tracking == 'lot' and not move.product_id.di_cons:
                                            lotexist = self.env['stock.production.lot'].search(['&', ('name', '=', move.purchase_line_id.order_id.name), ('product_id', '=', move.product_id.id)])
                                            if not lotexist:
                                                data = {
                                                'name': move.purchase_line_id.order_id.name,
                                                'product_id' : move.product_id.id                                      
                                                }            
                                                
                                                lot = self.env['stock.production.lot'].create(data)  # création du lot
                                                #self.env.cr.commit()# SC 23/08/2018 : Pas nécessaire de faire le commit pour que l'enreg soit utilisé       
                                                                       
                                                vals['lot_id'] = lot.id 
                                                vals['lot_name'] = lot.name
                                            else:
                                                vals['lot_id'] = lotexist.id 
                                                vals['lot_name'] = lotexist.name
                                        
                            
                        if not vals.get('lot_id') and  move.product_id.tracking != 'none':   
                            if move.product_id.tracking == 'lot' and not move.product_id.di_cons:         
                                picking = self.env['stock.picking'].browse(vals['picking_id'])
                                lotexist = self.env['stock.production.lot'].search(['&', ('name', '=', picking.name), ('product_id', '=', move.product_id.id)])
                                if not lotexist:
                                    data = {
                                    'name': picking.name,
                                    'product_id' : move.product_id.id                                        
                                    } 
                                    lot = self.env['stock.production.lot'].create(data)
                                    #self.env.cr.commit() # SC 23/08/2018 : Pas nécessaire de faire le commit pour que l'enreg soit utilisé
                                    vals['lot_id'] = lot.id
                                    vals['lot_name'] = lot.name
                                else:
                                    vals['lot_id'] = lotexist.id
                                    vals['lot_name'] = lotexist.name
                                
                elif picking.picking_type_id.code == 'outgoing':
                    if vals.get('lot_id') :
                        if not vals.get('di_lot_prod') :
                            vals['di_lot_prod']= self.di_get_lot_prod(vals['product_id'],vals['lot_id'])
                        
#                     if vals.get('move_id') :  # si on a une commande liée
#                         if vals['move_id'] != False:            
#                             move = self.env['stock.move'].browse(vals['move_id'])
#                             if move.sale_line_id:
#                                 if move.sale_line_id.di_station_id:
#                                     vals['location_id']=move.sale_line_id.di_station_id.id
                    
        ml = super(StockMoveLine, self).create(vals)
        return ml
    
    @api.multi
    def write(self, vals):
        for ml in self:    
            pick_id = False        
            if  (not vals.get('di_lot_prod') and not ml.di_lot_prod) :#or (vals.get('di_lot_prod')  and (vals['di_lot_prod']=='' or vals['di_lot_prod']==False)):
                if vals.get('picking_id'):
                    if vals['picking_id'] != False:
                        pick_id = vals['picking_id']
                if not pick_id:
                    if ml.picking_id:
                        if ml.picking_id != False:
                            pick_id = ml.picking_id.id
                     
                if pick_id :             
                    picking = ml.env['stock.picking'].browse(pick_id)
                    if picking.picking_type_id.code == 'outgoing': 
                        lot_id = False
                        if vals.get('lot_id') :
                            if vals['lot_id'] != False:
                                lot_id = vals['lot_id']
                        if not lot_id:
                            if ml.lot_id:
                                if ml.lot_id != False:
                                    lot_id = ml.lot_id.id
                                     
                         
                        if lot_id :     
                            if vals.get('product_id') and vals['product_id'] != False:
                                product_id = vals['product_id']  
                            else:
                                product_id = ml.product_id.id     
                            vals['di_lot_prod']= ml.di_get_lot_prod(product_id,lot_id)
                       
        res = super(StockMoveLine, self).write(vals)
    
        return res
  
    @api.multi                     
    @api.onchange('lot_id')
    def _di_change_lot_prod(self):
        if self.ensure_one():            
            if self.picking_id.picking_type_id.code == 'outgoing':                
                if self.lot_id:
                    if not self.di_lot_prod:
                        self.di_lot_prod = self.di_get_lot_prod(self.product_id.id,self.lot_id.id)
    