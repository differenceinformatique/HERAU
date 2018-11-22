# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from math import ceil
from datetime import  datetime
from odoo.addons import decimal_precision as dp
 
class StockMove(models.Model):
    _inherit = "stock.move"
    
    modifparprg = False

    di_qte_un_saisie = fields.Float(string='Quantité en unité de saisie', store=True,compute='_compute_quantites')
    di_un_saisie = fields.Selection([("PIECE", "Pièce"), ("COLIS", "Colis"), ("PALETTE", "Palette"), ("KG", "Kg")], string="Unité de saisie", store=True)
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
    
    di_spe_saisissable = fields.Boolean(string='Champs spé saisissables',default=False,compute='_di_compute_spe_saisissable',store=True)
    
    @api.multi
    @api.depends('sale_line_id','purchase_line_id')
    def _di_compute_champs_cde_init(self):       
        for sm in self:  
            if sm.sale_line_id :              
                sm.di_qte_un_saisie_init = sm.sale_line_id.di_qte_un_saisie
                sm.di_un_saisie_init = sm.sale_line_id.di_un_saisie
                sm.di_type_palette_init_id = sm.sale_line_id.di_type_palette_id
                sm.di_nb_pieces_init = sm.sale_line_id.di_nb_pieces
                sm.di_nb_colis_init = sm.sale_line_id.di_nb_colis
                sm.di_nb_palette_init = sm.sale_line_id.di_nb_palette
                sm.di_poin_init = sm.sale_line_id.di_poin
                sm.di_poib_init = sm.sale_line_id.di_poib
                sm.di_tare_init = sm.sale_line_id.di_tare
                sm.di_product_packaging_init_id = sm.sale_line_id.product_packaging 
            elif sm.purchase_line_id:
                sm.di_qte_un_saisie_init = sm.purchase_line_id.di_qte_un_saisie
                sm.di_un_saisie_init = sm.purchase_line_id.di_un_saisie
                sm.di_type_palette_init_id = sm.purchase_line_id.di_type_palette_id
                sm.di_nb_pieces_init = sm.purchase_line_id.di_nb_pieces
                sm.di_nb_colis_init = sm.purchase_line_id.di_nb_colis
                sm.di_nb_palette_init = sm.purchase_line_id.di_nb_palette
                sm.di_poin_init = sm.purchase_line_id.di_poin
                sm.di_poib_init = sm.purchase_line_id.di_poib
                sm.di_tare_init = sm.purchase_line_id.di_tare
                sm.di_product_packaging_init_id = sm.purchase_line_id.product_packaging
            
    
    
    @api.multi
    @api.depends('product_id.di_spe_saisissable','sale_line_id','product_id.product_tmpl_id.tracking')
    def _di_compute_spe_saisissable(self): 
        for sm in self:      
            if (sm.sale_line_id or sm.purchase_line_id)and sm.product_id.product_tmpl_id.tracking != 'none':
                sm.di_spe_saisissable = False
            else :                        
                sm.di_spe_saisissable = sm.product_id.di_spe_saisissable
     
        
    def action_show_details(self):
        # copie standard
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
#         #ajout des calculs sur les champs spé
#         for line in self.mapped('sale_line_id'):
#             line.qty_delivered = line._get_delivered_qty()
#             line.di_qte_un_saisie_liv = line._get_qte_un_saisie_liv()
#             line.di_nb_pieces_liv     = line._get_nb_pieces_liv()
#             line.di_nb_colis_liv      = line._get_nb_colis_liv()
#             line.di_nb_palette_liv    = line._get_nb_palettes_liv()
#             line.di_poin_liv          = line._get_poin_liv()
#             line.di_poib_liv          = line._get_poib_liv()
#             dimoves = self.env['stock.move'].search([('sale_line_id', '=', line.id)])
#             for dimove in dimoves:                                                    
#                 line.di_type_palette_liv_id  = dimove.di_type_palette_id
#                 line.di_un_saisie_liv     = dimove.di_un_saisie
#                 line.di_product_packaging_liv_id = dimove.di_product_packaging_id
#                 line.di_tare_liv          = dimove.di_tare
           
     
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
                    
                    
                elif move.di_un_saisie =="KG":
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
            if self.picking_partner_id and self.product_id:
                ref = self.env['di.ref.art.tiers'].search([('di_partner_id','=',self.picking_partner_id.id),('di_product_id','=',self.product_id.id)],limit=1)
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
           

            
    @api.model
    def create(self, vals):               
        di_avec_sale_line_id = False  # initialisation d'une variable       
#         di_ctx = dict(self._context or {})  # chargement du contexte
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
        
        
        if vals.get('purchase_line_id'):    
            purchaseline = self.env['purchase.order.line'].search([('id', '=', vals["purchase_line_id"])], limit=1)            
            if purchaseline.id != False: 
                vals["di_tare"] = purchaseline.di_tare   
                vals["di_un_saisie"] = purchaseline.di_un_saisie
                vals["di_type_palette_id"] = purchaseline.di_type_palette_id.id
                vals["di_product_packaging_id"] = purchaseline.product_packaging.id 
                
                     
                                                     
        res = super(StockMove, self).create(vals)    
        
                               
        if res.picking_type_id.code=='incoming':#1: # 1 correspond à une réception, 5 à un envoi. Il y en a d'autres mais qui n'ont pas l'air de servir pour le moment.  
            #en création directe de BL, cela ne génère par de "ventilation". Je la génère pour pouvoir attribuer le lot en auto sur les achats
            if res.move_line_ids.id==False and  res.purchase_line_id.order_id.id ==False: # si on confirme une commande d'achat, la ligne est déjà créée
                vals=res._prepare_move_line_vals(quantity=res.product_qty - res.reserved_availability)
#                 if vals.get('purchase_line_id'):
#                     Dipurchaseorderline = self.env['purchase.order.line'].search([('id', '=', vals["purchase_line_id"])], limit=1)
#                     if Dipurchaseorderline:
#                         vals["di_tare"] = Dipurchaseorderline.di_tare   
#                         vals["di_un_saisie"] = Dipurchaseorderline.di_un_saisie
#                         vals["di_type_palette_id"] = Dipurchaseorderline.di_type_palette_id.id
#                         vals["di_product_packaging_id"] = Dipurchaseorderline.product_packaging.id                                                         
#                         vals["di_flg_modif_uom"]=Dipurchaseorderline.di_flg_modif_uom
                self.env['stock.move.line'].create(vals)

        return res
    
    def di_somme_quantites_montants(self,product_id,date =False,cde_ach=False):
        qte =0.0
        mont =0.0
        nbcol =0.0
        nbpal = 0.0
        nbpiece =0.0
        poids = 0.0
        if cde_ach:
            if date:                                
    #             mouvs=self.env['stock.move'].search(['&',('product_id','=',product_id),('state','=','done'),('picking_id','!=',False),('picking_id.date_done','=',date),('product_uom_qty','!=',0.0)])
                mouvs=self.env['stock.move'].search(['&',('product_id','=',product_id),('state','in',('done','assigned')),('picking_id','!=',False)]).filtered(lambda mv: (mv.picking_id.date_done and mv.picking_id.date_done.date() == date) or (mv.picking_id.scheduled_date and mv.picking_id.scheduled_date.date() == date))
            else:
                mouvs=self.env['stock.move'].search([('product_id','=',product_id),('state','in',('done','assigned')),('picking_id','!=',False)])
        else:
            if date:
    #             mouvs=self.env['stock.move'].search(['&',('product_id','=',product_id),('state','=','done'),('picking_id','!=',False),('picking_id.date_done','=',date),('product_uom_qty','!=',0.0)])
                mouvs=self.env['stock.move'].search(['&',('product_id','=',product_id),('state','=','done'),('picking_id','!=',False)]).filtered(lambda mv: mv.picking_id.date_done.date() == date)
            else:
                mouvs=self.env['stock.move'].search([('product_id','=',product_id),('state','=','done'),('picking_id','!=',False)])
             
        for mouv in mouvs:
            if mouv.picking_type_id.code=='incoming':
                qte = qte + mouv.product_uom_qty
                nbcol = nbcol + mouv.di_nb_colis
                nbpal = nbpal + mouv.di_nb_palette
                nbpiece = nbpiece + mouv.di_nb_pieces
                poids = poids + mouv.di_poin
                if mouv.purchase_line_id:
                    mont = mont + mouv.purchase_line_id.price_subtotal
                elif mouv.sale_line_id:
                    mont = mont + (mouv.sale_line_id.product_uom_qty * mouv.sale_line_id.purchase_price)
            else:
                qte = qte - mouv.product_uom_qty
                nbcol = nbcol - mouv.di_nb_colis
                nbpal = nbpal - mouv.di_nb_palette
                nbpiece = nbpiece - mouv.di_nb_pieces
                poids = poids - mouv.di_poin
                if mouv.purchase_line_id:
                    mont = mont - mouv.purchase_line_id.price_subtotal
                elif mouv.sale_line_id:
                    mont = mont - (mouv.sale_line_id.product_uom_qty * mouv.sale_line_id.purchase_price)
          
        if date:

            mouvs=self.env['stock.move'].search(['&',('product_id','=',product_id),('state','=','done'),('picking_id','=',False)]).filtered(lambda mv: mv.inventory_id.date.date() == date)
        else:
            mouvs=self.env['stock.move'].search([('product_id','=',product_id),('state','=','done'),('picking_id','=',False)])
             
        for mouv in mouvs:
#             if mouv.remaining_qty:
            if mouv.location_dest_id.usage == 'internal':
                qte = qte + mouv.product_uom_qty
                nbcol = nbcol + mouv.di_nb_colis
                nbpal = nbpal + mouv.di_nb_palette
                nbpiece = nbpiece + mouv.di_nb_pieces
                poids = poids + mouv.di_poin
            else:
                qte = qte - mouv.product_uom_qty 
                nbcol = nbcol - mouv.di_nb_colis
                nbpal = nbpal - mouv.di_nb_palette
                nbpiece = nbpiece - mouv.di_nb_pieces
                poids = poids - mouv.di_poin                       
                
        return (qte,mont,nbcol,nbpal,nbpiece,poids)
                 
class StockMoveLine(models.Model):
    _inherit = "stock.move.line"
      
    di_qte_un_saisie = fields.Float(string='Quantité en unité de saisie', store=True,compute="_compute_qte_un_saisie")          
    di_nb_pieces = fields.Integer(string='Nb pièces', store=True)
    di_nb_colis = fields.Integer(string='Nb colis' ,store=True)
    di_nb_palette = fields.Float(string='Nb palettes', store=True, digits=dp.get_precision('Product Unit of Measure'))
    di_poin = fields.Float(string='Poids net' , store=True)
    di_poib = fields.Float(string='Poids brut', store=True)
    di_tare = fields.Float(string='Tare', store=True)#,compute="_compute_tare")    
    di_flg_modif_uom = fields.Boolean(default=False)
    
    di_spe_saisissable = fields.Boolean(string='Champs spé saisissables',default=False,compute='_di_compute_spe_saisissable',store=True)
    
    @api.multi
    @api.onchange('move_id.di_type_palette_id','move_id.di_product_packaging_id','di_nb_colis','di_nb_palette')
    def _compute_tare(self):        
        self.di_tare = (self.move_id.di_type_palette_id.di_poids * self.di_nb_palette) + (self.move_id.di_product_packaging_id.di_poids * self.di_nb_colis)
        
    @api.multi
    @api.depends('product_id.di_spe_saisissable')
    def _di_compute_spe_saisissable(self):   
        for sml in self:     
            sml.di_spe_saisissable =sml.product_id.di_spe_saisissable
     
        
    @api.multi    
    @api.depends('di_poib','di_tare','di_nb_colis','di_nb_pieces','di_nb_palette')
    def _compute_qte_un_saisie(self):
        #recalcule la quantité en unité de saisie
        for sml in self:
            if not sml.move_id.inventory_id:
                if self._context.get('di_move_id'):
                    move = self.env['stock.move'].browse(self._context['di_move_id'])
                else:
                    move = sml.move_id
                 
                if move.di_un_saisie == "PIECE":
                    sml.di_qte_un_saisie = sml.di_nb_pieces
                elif move.di_un_saisie == "COLIS":
                    sml.di_qte_un_saisie = sml.di_nb_colis
                elif move.di_un_saisie == "PALETTE":
                    sml.di_qte_un_saisie = sml.di_nb_palette
                elif move.di_un_saisie == "KG":
                    sml.di_qte_un_saisie = sml.di_poib
                else:
                    sml.di_qte_un_saisie = sml.qty_done   
                       
    
    @api.multi                     
    @api.onchange('di_nb_palette')
    def _di_change_nb_palette(self):
        if self.ensure_one()and not self.move_id.inventory_id:   
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
        if self.ensure_one()and not self.move_id.inventory_id:      
            if self._context.get('di_move_id'):
                move = self.env['stock.move'].browse(self._context['di_move_id'])
            else:
                move = self.move_id
#             if move.di_un_saisie == "COLIS":                         
            self.qty_done = move.di_product_packaging_id.qty * self.di_nb_colis                 
            self.di_nb_pieces = ceil(move.di_product_packaging_id.di_qte_cond_inf * self.di_nb_colis)
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
        if self.ensure_one()and not self.move_id.inventory_id:
            self.di_tare = self.di_poib - self.di_poin
    @api.multi                     
    @api.onchange('di_tare')
    def _di_change_tare(self):
        if self.ensure_one()and not self.move_id.inventory_id:
            self.di_poib = self.di_poin + self.di_tare
            
            
    @api.multi                     
    @api.onchange('di_poin')
    def _di_change_poin(self):
        if self.ensure_one()and not self.move_id.inventory_id:  
            if self._context.get('di_move_id'):
                move = self.env['stock.move'].browse(self._context['di_move_id'])
            else:
                move = self.move_id    
#             if move.di_un_saisie == "KG":
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
        if self.ensure_one() and not self.move_id.inventory_id:
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
                if picking.picking_type_id.code=='incoming': 
                    
#                     if vals.get('move_id') : # si on a une commande liée
#                         if vals['move_id']!=False:            
#                             move = self.env['stock.move'].browse(vals['move_id'])
#                             if move.purchase_line_id:                       
#                                 vals["di_tare"] = move.purchase_line_id.di_tare   
#                                 vals["di_un_saisie"] = move.purchase_line_id.di_un_saisie
#                                 vals["di_type_palette_id"] = move.purchase_line_id.di_type_palette_id.id
#                                 vals["di_product_packaging_id"] = move.purchase_line_id.product_packaging.id                                                                                             
                            
                                       
                    if not vals.get('lot_id'): #si pas de lot saisi
                        if vals.get('move_id') : # si on a une commande liée
                            if vals['move_id']!=False:            
                                move = self.env['stock.move'].browse(vals['move_id'])
                                if move.product_id.tracking != 'none':
                                    if move.purchase_line_id.order_id.id !=False:
                                        lotexist = self.env['stock.production.lot'].search(['&',('name','=',move.purchase_line_id.order_id.name),('product_id','=',move.product_id.id)])
                                        if not lotexist:
                                            data = {
                                            'name': move.purchase_line_id.order_id.name,  
                                            'product_id' : move.product_id.id                                      
                                            }            
                                            
                                            lot = self.env['stock.production.lot'].create(data)       # création du lot
                                            #self.env.cr.commit()# SC 23/08/2018 : Pas nécessaire de faire le commit pour que l'enreg soit utilisé       
                                                                   
                                            vals['lot_id']=lot.id 
                                            vals['lot_name']=lot.name
                                        else:
                                            vals['lot_id']=lotexist.id 
                                            vals['lot_name']=lotexist.name
                            
                        if not vals.get('lot_id') and  move.product_id.tracking != 'none':            
                            picking = self.env['stock.picking'].browse(vals['picking_id'])
                            lotexist = self.env['stock.production.lot'].search(['&',('name','=',picking.name),('product_id','=',move.product_id.id)])
                            if not lotexist:
                                data = {
                                'name': picking.name,
                                'product_id' : move.product_id.id                                        
                                } 
                                lot = self.env['stock.production.lot'].create(data)
                                #self.env.cr.commit()# SC 23/08/2018 : Pas nécessaire de faire le commit pour que l'enreg soit utilisé
                                vals['lot_id']=lot.id
                                vals['lot_name']=lot.name
                            else:
                                vals['lot_id']=lotexist.id
                                vals['lot_name']=lotexist.name
                                

        ml = super(StockMoveLine, self).create(vals)
        return ml
    
    def di_qte_spe_en_stock(self,product_id,date,lot):            
        nbcol =0.0
        nbpal = 0.0
        nbpiece =0.0
        poids = 0.0
        qte_std = 0.0    
        if date:
#             mouvs=self.env['stock.move'].search(['&',('product_id','=',product_id),('state','=','done'),('picking_id','!=',False),('picking_id.date_done','=',date),('product_uom_qty','!=',0.0)])
            mouvs=self.env['stock.move.line'].search(['&',('product_id','=',product_id.id),('lot_id','=',lot.id),('move_id.state','=','done'),('move_id.picking_id','!=',False)]).filtered(lambda mv: mv.move_id.picking_id.date_done.date() <= date)
        else:
            mouvs=self.env['stock.move.line'].search([('product_id','=',product_id.id),('lot_id','=',lot.id),('move_id.state','=','done'),('picking_id','!=',False)])
             
        for mouv in mouvs:
            if mouv.move_id.picking_type_id.code=='incoming':                
                nbcol = nbcol + mouv.di_nb_colis
                nbpal = nbpal + mouv.di_nb_palette
                nbpiece = nbpiece + mouv.di_nb_pieces
                poids = poids + mouv.di_poin
                qte_std = qte_std + mouv.qty_done  				              
            else:                
                nbcol = nbcol - mouv.di_nb_colis
                nbpal = nbpal - mouv.di_nb_palette
                nbpiece = nbpiece - mouv.di_nb_pieces
                poids = poids - mouv.di_poin
                qte_std = qte_std - mouv.qty_done  				                        
        if date:
#             mouvs=self.env['stock.move'].search(['&',('product_id','=',product_id),('state','=','done'),('picking_id','=',False),('inventory_id.date','=',date),('product_uom_qty','!=',0.0)])
            mouvs=self.env['stock.move.line'].search(['&',('product_id','=',product_id.id),('lot_id','=',lot.id),('move_id.state','=','done'),('move_id.picking_id','=',False)]).filtered(lambda mv: mv.move_id.inventory_id.date.date() <= date)
        else:
            mouvs=self.env['stock.move.line'].search([('product_id','=',product_id.id),('lot_id','=',lot.id),('move_id.state','=','done'),('move_id.picking_id','=',False)])
             
        for mouv in mouvs:
#             if mouv.move_id.remaining_qty:
            if mouv.location_dest_id.usage == 'internal':                
                nbcol = nbcol + mouv.di_nb_colis
                nbpal = nbpal + mouv.di_nb_palette
                nbpiece = nbpiece + mouv.di_nb_pieces
                poids = poids + mouv.di_poin
                qte_std = qte_std + mouv.qty_done	                
            else:                
                nbcol = nbcol - mouv.di_nb_colis
                nbpal = nbpal - mouv.di_nb_palette
                nbpiece = nbpiece - mouv.di_nb_pieces
                poids = poids - mouv.di_poin
                qte_std = qte_std - mouv.qty_done                       				
                
        return (nbcol,nbpal,nbpiece,poids,qte_std)
    
    
class StockPicking(models.Model):
    _inherit = 'stock.picking'
    
    di_nbpal = fields.Float(compute='_compute_di_nbpal_nbcol', store=True, digits=dp.get_precision('Product Unit of Measure'))
    di_nbcol = fields.Integer(compute='_compute_di_nbpal_nbcol', store=True)
    di_poin = fields.Float(compute='_compute_di_nbpal_nbcol', store=True, digits=dp.get_precision('Product Unit of Measure'))
    di_tournee = fields.Char(string="Tournée",compute='_compute_tournee',store=True)
    di_rangtournee = fields.Char(string="Rang dans la tournée",compute='_compute_tournee',store=True)
    di_nbex = fields.Integer("Nombre exemplaires",help="""Nombre d'exemplaires d'une impression.""",default=0)
    
#     @api.model
#     def di_get_nbex_partner(self):
#         if self.partner_id:
#             return self.partner_id.di_nbex
#         else:
#             return 1
    @api.model
    def create(self,vals):        
        res = super(StockPicking, self).create(vals)        
        for sp in res:   
            if sp.di_nbex==0: 
                if sp.partner_id:                
                    sp.write({'di_nbex': sp.partner_id.di_nbex_bl})                
        return res
        
        
    @api.multi
    @api.onchange("partner_id")
    def di_onchange_partner(self):
        for bl in self:
            if bl.partner_id:
                bl.di_nbex = bl.partner_id.di_nbex_bl
    
    @api.depends('move_lines')
    def _compute_di_nbpal_nbcol(self):
        for picking in self:
            wnbpal = sum(move.di_nb_palette for move in picking.move_lines if move.state != 'cancel')
            wnbcol = sum(move.di_nb_colis for move in picking.move_lines if move.state != 'cancel')
            wpoin = sum(move.di_poin for move in picking.move_lines if move.state != 'cancel')
            picking.di_nbpal = wnbpal
            picking.di_nbcol = ceil(wnbcol)
            picking.di_poin = wpoin
        
    @api.depends('name')
    def _compute_tournee(self):
        for sp in self:
            # pour éviter erreur de tri à l'édition du bordereau de transport
            sp.di_tournee = " "
            sp.di_rangtournee = " "
            so = self.env['sale.order'].search([('name', '=', sp.origin)])
            if so:
                if so.di_tournee:
                    sp.di_tournee = so.di_tournee
                if so.di_rangtournee:
                    sp.di_rangtournee = so.di_rangtournee


        
class StockQuant(models.Model):
    _inherit = 'stock.quant'
    
    di_cmp = fields.Float(string="Coût moyen",related="product_id.standard_price",group_operator='avg',store=True)
    di_valstock = fields.Float(string='Valeur Stock',compute='_compute_valstock',group_operator='sum',store=True)
    di_nb_pieces    = fields.Integer(string='Nb pièces' ,compute="_compute_qte_spe",group_operator='sum',store=True)
    di_nb_colis     = fields.Integer(string='Nb colis',compute="_compute_qte_spe",group_operator='sum',store=True)
    di_poin         = fields.Float(string='Poids net',compute="_compute_qte_spe",group_operator='sum',store=True)
    currency_id = fields.Many2one("res.currency", related='company_id.currency_id', string="Currency")   # pour avoir le widget euro
    
    @api.multi
    @api.depends('di_cmp','quantity')
    def _compute_valstock(self):
        for quant in self:
            quant.di_valstock = quant.quantity*quant.di_cmp
        
    @api.multi
    @api.depends('quantity')
    def _compute_qte_spe(self):
        for quant in self:
            quant.di_poin = quant.quantity*quant.product_id.weight                        
            if quant.product_id.di_type_colis_id.qty != 0.0:
                quant.di_nb_colis = ceil(quant.quantity / quant.product_id.di_type_colis_id.qty)
            else:
                quant.di_nb_colis = ceil(quant.quantity)
            if quant.product_id.di_type_palette_id.di_qte_cond_inf !=0.0:    
                quant.di_nb_palette = quant.di_nb_colis / quant.product_id.di_type_palette_id.di_qte_cond_inf
            else:  
                quant.di_nb_palette = quant.di_nb_colis
        self.di_nb_pieces = ceil(self.product_id.di_type_colis_id.di_qte_cond_inf * self.di_nb_colis)