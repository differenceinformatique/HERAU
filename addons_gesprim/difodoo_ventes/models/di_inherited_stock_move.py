# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from difodoo.addons_gesprim.difodoo_ventes.models.di_outils import *
from math import *
 
class StockMove(models.Model):
    _inherit = "stock.move"
    
    modifparprg = False
     
    di_qte_un_saisie = fields.Float(string='Quantité en unité de saisie', store=True,compute='_compute_quantites')
    di_un_saisie = fields.Selection([("PIECE", "Pièce"), ("COLIS", "Colis"), ("PALETTE", "Palette"), ("POIDS", "Poids")], string="Unité de saisie", store=True)
    di_type_palette_id = fields.Many2one('product.packaging', string='Palette', store=True) 
    di_nb_pieces = fields.Integer(string='Nb pièces', store=True,compute='_compute_quantites')
    di_nb_colis = fields.Integer(string='Nb colis' , store=True,compute='_compute_quantites')
    di_nb_palette = fields.Float(string='Nb palettes' , store=True,compute='_compute_quantites')
    di_poin = fields.Float(string='Poids net' , store=True,compute='_compute_quantites')
    di_poib = fields.Float(string='Poids brut', store=True,compute='_compute_quantites')
    di_tare = fields.Float(string='Tare', store=True,compute='_compute_quantites')
    di_product_packaging_id = fields.Many2one('product.packaging', string='Package', default=False, store=True)
    di_flg_modif_uom = fields.Boolean(default=False)
     
     
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
        
    def action_show_details(self):
        # surcharge pour ajouter un champ dans le contexte
        """ Returns an action that will open a form view (in a popup) allowing to work on all the
        move lines of a particular move. This form view is used when "show operations" is not
        checked on the picking type.
        """
        self.ensure_one()

        # If "show suggestions" is not checked on the picking type, we have to filter out the
        # reserved move lines. We do this by displaying `move_line_nosuggest_ids`. We use
        # different views to display one field or another so that the webclient doesn't have to
        # fetch both.
        if self.picking_id.picking_type_id.show_reserved:
            view = self.env.ref('stock.view_stock_move_operations')
        else:
            view = self.env.ref('stock.view_stock_move_nosuggest_operations')

        return {
            'name': _('Detailed Operations'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'stock.move',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',
            'res_id': self.id,
            'context': dict(
                self.env.context,
                show_lots_m2o=self.has_tracking != 'none' and (self.picking_type_id.use_existing_lots or self.state == 'done' or self.origin_returned_move_id.id),  # able to create lots, whatever the value of ` use_create_lots`.
                show_lots_text=self.has_tracking != 'none' and self.picking_type_id.use_create_lots and not self.picking_type_id.use_existing_lots and self.state != 'done' and not self.origin_returned_move_id.id,
                show_source_location=self.location_id.child_ids,
                show_destination_location=self.location_dest_id.child_ids,
                show_package=not self.location_id.usage == 'supplier',
                show_reserved_quantity=self.state != 'done',
                #Ajout de l'id du move pour pouvoir le récupérer dans le contexte en saisie des lots
                di_move_id=self.id
                
            ),
        }
    def _action_done(self):
        #standard de validadtion de livraison        
        result = super(StockMove, self)._action_done()
        #ajout des calculs sur les champs spé
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
           
     
        return result
    
    
    def _action_assign(self):
        """ Reserve stock moves by creating their stock move lines. A stock move is
        considered reserved once the sum of `product_qty` for all its move lines is
        equal to its `product_qty`. If it is less, the stock move is considered
        partially available.
        """
        super(StockMove, self)._action_assign()
        for move in self:
            for line in move.move_line_ids:
                line.di_tare = move.di_tare
                line.qty_done = line.product_uom_qty
                if move.di_un_saisie =="PIECE":
                    
                    if move.product_id.di_get_type_piece().qty != 0.0:
                        line.di_qte_un_saisie = line.qty_done / move.product_id.di_get_type_piece().qty
                    else:
                        line.di_qte_un_saisie = line.qty_done  
                        
                    line.di_nb_pieces = ceil(line.di_qte_un_saisie)   
                    if move.di_product_packaging_id.qty != 0.0 :
                        line.di_nb_colis = ceil(line.qty_done / move.di_product_packaging_id.qty)
                    else:      
                        line.di_nb_colis = ceil(line.qty_done)             
                    if move.di_type_palette_id.di_qte_cond_inf != 0.0:
                        line.di_nb_palette = line.di_nb_colis / move.di_type_palette_id.di_qte_cond_inf
                    else:
                        line.di_nb_palette = line.di_nb_colis
                    line.di_poin = line.qty_done * move.product_id.weight 
                    line.di_poib = line.di_poin + line.di_tare 
                      
                elif move.di_un_saisie =="COLIS":
                    
                    
                    if move.di_product_packaging_id.qty!=0.0:
                        line.di_qte_un_saisie = line.qty_done / move.di_product_packaging_id.qty
                    else:
                        line.di_qte_un_saisie = line.qty_done 
                        
                    line.di_nb_colis = ceil(line.di_qte_un_saisie)
                        
                    line.di_nb_pieces = ceil(move.di_product_packaging_id.di_qte_cond_inf * line.di_nb_colis)
                    if move.di_type_palette_id.di_qte_cond_inf != 0.0:                
                        line.di_nb_palette = line.di_nb_colis / move.di_type_palette_id.di_qte_cond_inf
                    else:
                        line.di_nb_palette = line.di_nb_colis
                    line.di_poin = line.qty_done * move.product_id.weight 
                    line.di_poib = line.di_poin + line.di_tare
                                        
                elif move.di_un_saisie =="PALETTE":
                    if move.di_type_palette_id.qty!=0.0:
                        line.di_qte_un_saisie = line.qty_done / move.di_type_palette_id.qty
                    else:
                        line.di_qte_un_saisie = line.qty_done 
                        
                    line.di_nb_palette = line.di_qte_un_saisie
                    
                    if move.di_type_palette_id.di_qte_cond_inf != 0.0:
                        line.di_nb_colis = ceil(line.di_nb_palette / move.di_type_palette_id.di_qte_cond_inf)
                    else:
                        line.di_nb_colis = ceil(line.di_nb_palette)
                    line.di_nb_pieces = ceil(move.di_product_packaging_id.di_qte_cond_inf * line.di_nb_colis)
                    
                    line.di_poin = line.qty_done * move.product_id.weight 
                    line.di_poib = line.di_poin + line.di_tare
                    
                    
                elif move.di_un_saisie =="POIDS":
                    if move.product_id.weight !=0.0:
                        line.di_qte_un_saisie = line.qty_done / move.product_id.weight 
                    else:
                        line.di_qte_un_saisie = line.qty_done
                        
                
                    line.di_poin = line.di_qte_un_saisie
                    line.di_poib = line.di_poin + line.di_tare
                    if move.di_product_packaging_id.qty != 0.0:
                        line.di_nb_colis = ceil(line.qty_done / move.di_product_packaging_id.qty)
                    else:
                        line.di_nb_colis = ceil(line.qty_done)
                    if move.di_type_palette_id.di_qte_cond_inf != 0.0:    
                        line.di_nb_palette = line.di_nb_colis / move.di_type_palette_id.di_qte_cond_inf
                    else:  
                        line.di_nb_palette = line.di_nb_colis
                    line.di_nb_pieces = ceil(move.di_product_packaging_id.di_qte_cond_inf * line.di_nb_colis)
                    
                else :
                    if move.product_id.weight !=0.0:
                        line.di_qte_un_saisie = line.qty_done / move.product_id.weight 
                    else:
                        line.di_qte_un_saisie = line.qty_done
                        
                
                    line.di_poin = line.di_qte_un_saisie
                    line.di_poib = line.di_poin + line.di_tare
                    if move.di_product_packaging_id.qty != 0.0:
                        line.di_nb_colis = ceil(line.qty_done / move.di_product_packaging_id.qty)
                    else:
                        line.di_nb_colis = ceil(line.qty_done)
                    if move.di_type_palette_id.di_qte_cond_inf != 0.0:    
                        line.di_nb_palette = line.di_nb_colis / move.di_type_palette_id.di_qte_cond_inf
                    else:  
                        line.di_nb_palette = line.di_nb_colis
                    line.di_nb_pieces = ceil(move.di_product_packaging_id.di_qte_cond_inf * line.di_nb_colis)
                    
    @api.depends('move_line_ids.di_qte_un_saisie','move_line_ids.di_poin','move_line_ids.di_poib','move_line_ids.di_tare','move_line_ids.di_nb_colis','move_line_ids.di_nb_pieces','move_line_ids.di_nb_palette')
    def _compute_quantites(self):
        #recalcule la quantité en unité de saisie en fonction des ventils
        for move in self:
            for move_line in move._get_move_lines():                
                move.di_qte_un_saisie += move_line.di_qte_un_saisie
                move.di_poin += move_line.di_poin
                move.di_poib += move_line.di_poib
                move.di_tare += move_line.di_tare
                move.di_nb_colis += move_line.di_nb_colis
                move.di_nb_pieces += move_line.di_nb_pieces
                move.di_nb_palette += move_line.di_nb_palette 
                  
    @api.multi            
    @api.onchange('product_id')
    def _di_charger_valeur_par_defaut(self):
        if self.ensure_one():
            if self.product_id.id != False:
                self.di_un_saisie = self.product_id.di_un_saisie
                self.di_type_palette_id = self.product_id.di_type_palette_id
                self.di_product_packaging_id = self.product_id.di_type_colis_id

            
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
                    vals["di_product_packaging_id"] = Disaleorderline.product_packaging.id                                                         
                    vals["di_flg_modif_uom"]=Disaleorderline.di_flg_modif_uom
                    
                 
                                                     
        res = super(StockMove, self).create(vals)    
        
                               
        if res.picking_type_id.code=='incoming':#1: # 1 correspond à une réception, 5 à un envoi. Il y en a d'autres mais qui n'ont pas l'air de servir pour le moment.  
            #en création directe de BL, cela ne génère par de "ventilation". Je la génère pour pouvoir attribuer le lot en auto sur les achats
            if res.move_line_ids.id==False and  res.purchase_line_id.order_id.id ==False: # si on confirme une commande d'achat, la ligne est déjà créée
                self.env['stock.move.line'].create(res._prepare_move_line_vals(quantity=res.product_qty - res.reserved_availability))

        return res
 
class StockMoveLine(models.Model):
    _inherit = "stock.move.line"
      
    di_qte_un_saisie = fields.Float(string='Quantité en unité de saisie', store=True,compute="_compute_qte_un_saisie")          
    di_nb_pieces = fields.Integer(string='Nb pièces', store=True)
    di_nb_colis = fields.Integer(string='Nb colis' ,store=True)
    di_nb_palette = fields.Float(string='Nb palettes' , store=True)
    di_poin = fields.Float(string='Poids net' , store=True)
    di_poib = fields.Float(string='Poids brut', store=True)
    di_tare = fields.Float(string='Tare', store=True)    
    di_flg_modif_uom = fields.Boolean(default=False)
        
    @api.one    
    @api.depends('di_poib','di_tare','di_nb_colis','di_nb_pieces','di_nb_palette')
    def _compute_qte_un_saisie(self):
        #recalcule la quantité en unité de saisie
        if self._context.get('di_move_id'):
            move = self.env['stock.move'].browse(self._context['di_move_id'])
        else:
            move = self.move_id
         
        if move.di_un_saisie == "PIECE":
            self.di_qte_un_saisie = self.di_nb_pieces
        elif move.di_un_saisie == "COLIS":
            self.di_qte_un_saisie = self.di_nb_colis
        elif move.di_un_saisie == "PALETTE":
            self.di_qte_un_saisie = self.di_nb_palette
        elif move.di_un_saisie == "POIDS":
            self.di_qte_un_saisie = self.di_poib
        else:
            self.di_qte_un_saisie = self.qty_done   
                       
    
    @api.multi                     
    @api.onchange('di_nb_palette')
    def _di_change_nb_palette(self):
        if self.ensure_one():   
            if self._context.get('di_move_id'):
                move = self.env['stock.move'].browse(self._context['di_move_id'])
            else:
                move = self.move_id
#             if move.di_un_saisie == "PALETTE":                                         
            
            self.di_nb_colis = ceil(self.di_nb_palette * move.di_type_palette_id.di_qte_cond_inf)
            self.di_nb_pieces = ceil(move.di_product_packaging_id.di_qte_cond_inf * self.di_nb_colis)
            self.qty_done = move.di_product_packaging_id.qty * self.di_nb_colis
            self.di_poin = self.qty_done * move.product_id.weight 
            self.di_poib = self.di_poin + self.di_tare 
      
      
    @api.multi                     
    @api.onchange('di_nb_colis')
    def _di_change_nb_colis(self):
        if self.ensure_one():      
            if self._context.get('di_move_id'):
                move = self.env['stock.move'].browse(self._context['di_move_id'])
            else:
                move = self.move_id
#             if move.di_un_saisie == "COLIS":                         
            self.qty_done = move.di_product_packaging_id.qty * self.di_nb_colis                 
            self.di_nb_pieces = ceil(move.  di_product_packaging_id.di_qte_cond_inf * self.di_nb_colis)
            if move.di_type_palette_id.di_qte_cond_inf != 0.0:                
                self.di_nb_palette = self.di_nb_colis / move.di_type_palette_id.di_qte_cond_inf
            else:
                self.di_nb_palette = self.di_nb_colis
            self.di_poin = self.qty_done * move.product_id.weight 
            self.di_poib = self.di_poin + self.di_tare
#     @api.multi                     
#     @api.onchange('di_nb_pieces')
#     def _di_change_nb_pieces(self):
#         if self.ensure_one():
#             if self._context.get('di_move_id'):
#                 move = self.env['stock.move'].browse(self._context['di_move_id'])
#             else:
#                 move = self.move_id
#             if move.di_un_saisie == "PIECE":                           
#                 self.qty_done = self.product_id.di_get_type_piece().qty * self.di_nb_pieces                  
#                 if move.di_product_packaging_id.qty != 0.0 :
#                     self.di_nb_colis = ceil(self.qty_done / move.di_product_packaging_id.qty)
#                 else:      
#                     self.di_nb_colis = ceil(self.qty_done)             
#                 if move.di_type_palette_id.di_qte_cond_inf != 0.0:
#                     self.di_nb_palette = self.di_nb_colis / move.di_type_palette_id.di_qte_cond_inf
#                 else:
#                     self.di_nb_palette = self.di_nb_colis
#                 self.di_poin = self.qty_done * move.product_id.weight 
#                 self.di_poib = self.di_poin + self.di_tare
    @api.multi                     
    @api.onchange('di_poib')
    def _di_change_poib(self):
        if self.ensure_one():
            self.di_tare = self.di_poib - self.di_poin
    @api.multi                     
    @api.onchange('di_tare')
    def _di_change_tare(self):
        if self.ensure_one():
            self.di_poib = self.di_poin + self.di_tare
            
            
    @api.multi                     
    @api.onchange('di_poin')
    def _di_change_poin(self):
        if self.ensure_one():  
            if self._context.get('di_move_id'):
                move = self.env['stock.move'].browse(self._context['di_move_id'])
            else:
                move = self.move_id    
#             if move.di_un_saisie == "POIDS":
            self.di_poib = self.di_poin + self.di_tare
            
            
            if move.product_uom.name.lower() == 'kg':
                self.qty_done = self.di_poin
            
#             self.qty_done = self.di_poin
#             if move.di_product_packaging_id.qty != 0.0:
#                 self.di_nb_colis = ceil(self.qty_done / move.di_product_packaging_id.qty)
#             else:
#                 self.di_nb_colis = ceil(self.qty_done)
#             if move.di_type_palette_id.di_qte_cond_inf != 0.0:    
#                 self.di_nb_palette = self.di_nb_colis / move.di_type_palette_id.di_qte_cond_inf
#             else:  
#                 self.di_nb_palette = self.di_nb_colis
#             self.di_nb_pieces = ceil(move.di_product_packaging_id.di_qte_cond_inf * self.di_nb_colis)
             
             
    @api.multi                     
    @api.onchange('qty_done')
    def _di_change_qty_done(self):
        if self.ensure_one():
            if self._context.get('di_move_id'):
                move = self.env['stock.move'].browse(self._context['di_move_id'])
            else:
                move = self.move_id
            if move.product_uom.name.lower() == 'kg':
                self.di_poin = self.qty_done
            
            
                 
            
    @api.model
    def create(self, vals):
        if vals.get('picking_id') :
            if vals['picking_id']!=False:                  
                picking = self.env['stock.picking'].browse(vals['picking_id'])
                if picking.picking_type_id.code=='incoming': # 1 correspond à une réception, 5 à un envoi. Il y en a d'autres mais qui n'ont pas l'air de servir pour le moment.               
                    if not vals.get('lot_id'): #si pas de lot saisi
                        if vals.get('move_id') : # si on a une commande liée
                            if vals['move_id']!=False:            
                                move = self.env['stock.move'].browse(vals['move_id'])
                                if move.purchase_line_id.order_id.id !=False:
                                    data = {
                                    'name': move.purchase_line_id.order_id.name,  
                                    'product_id' : move.product_id.id                                      
                                    }            
                                    lot = self.env['stock.production.lot'].create(data)       # création du lot                              
                                    vals['lot_id']=lot.id 
                                    vals['lot_name']=lot.name
                            
                        if not vals.get('lot_id'):            
                            picking = self.env['stock.picking'].browse(vals['picking_id'])
                            data = {
                            'name': picking.name,
                            'product_id' : move.product_id.id                                        
                            } 
                            lot = self.env['stock.production.lot'].create(data)
                            vals['lot_id']=lot.id
                            vals['lot_name']=lot.name

        ml = super(StockMoveLine, self).create(vals)
        return ml