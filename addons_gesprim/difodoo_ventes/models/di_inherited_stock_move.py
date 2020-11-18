# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from math import ceil
from datetime import  datetime
from odoo.addons import decimal_precision as dp
from odoo.tools.float_utils import float_round
from odoo.tools import float_utils

 
class StockMove(models.Model):
    _inherit = "stock.move"

    di_qte_un_saisie = fields.Float(string='Quantité en unité de saisie', store=True, compute='_compute_quantites')
    di_un_saisie = fields.Selection([("PIECE", "Pièce"), ("COLIS", "Colis"), ("PALETTE", "Palette"), ("KG", "Kg")], string="Unité de saisie", store=True)
    di_type_palette_id = fields.Many2one('product.packaging', string='Palette', store=True) 
    di_nb_pieces = fields.Integer(string='Nb pièces', store=True, compute='_compute_quantites')
    di_nb_colis = fields.Float(string='Nb colis' , store=True, compute='_compute_quantites', digits=(8,1))
    di_nb_palette = fields.Float(string='Nb palettes' , store=True, compute='_compute_quantites')
    di_poin = fields.Float(string='Poids net' , store=True, compute='_compute_quantites')
    di_poib = fields.Float(string='Poids brut', store=True, compute='_compute_quantites')
    di_tare = fields.Float(string='Tare', store=True, compute='_compute_quantites')
    di_product_packaging_id = fields.Many2one('product.packaging', string='Package', default=False, store=True)
    di_flg_modif_uom = fields.Boolean(default=False)
     
    di_qte_un_saisie_init = fields.Float(related="sale_line_id.di_qte_un_saisie")
    di_un_saisie_init = fields.Selection(related="sale_line_id.di_un_saisie")
    di_type_palette_init_id = fields.Many2one(related="sale_line_id.di_type_palette_id") 
    di_nb_pieces_init = fields.Integer(related="sale_line_id.di_nb_pieces")
    di_nb_colis_init = fields.Float(related="sale_line_id.di_nb_colis", digits=(8,1))
    di_nb_palette_init = fields.Float(related="sale_line_id.di_nb_palette")
    di_poin_init = fields.Float(related="sale_line_id.di_poin")
    di_poib_init = fields.Float(related="sale_line_id.di_poib")
    di_tare_init = fields.Float(related="sale_line_id.di_tare")
    di_product_packaging_init_id = fields.Many2one(related="sale_line_id.product_packaging")
    
    di_prix_ac = fields.Float(related="purchase_line_id.price_unit")
    
        
    
    di_spe_saisissable = fields.Boolean(string='Champs spé saisissables', default=False, compute='_di_compute_spe_saisissable', store=True)
    
    @api.multi
    @api.depends('sale_line_id', 'purchase_line_id')
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
    @api.depends('product_id.di_spe_saisissable', 'sale_line_id', 'product_id.product_tmpl_id.tracking')
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
                # Ajout de l'id du move pour pouvoir le récupérer dans le contexte en saisie des lots
                di_move_id=self.id
                
            ),
        }

    def _action_done(self):
        # standard de validadtion de livraison        
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
                line.qty_done = line.product_uom_qty
                if move.picking_type_id.code == 'outgoing':
                    if move.sale_line_id:
                        if  move.sale_line_id.product_uom_qty != 0.0:
                            ratio = line.product_uom_qty / move.sale_line_id.product_uom_qty
                        else:
                            ratio = 1
                        line.di_nb_pieces = ceil(move.sale_line_id.di_nb_pieces * ratio)
                        line.di_nb_colis = round(move.sale_line_id.di_nb_colis * ratio,1)
                        nbcol = round(line.di_nb_colis,1)
                        line.di_poin = move.sale_line_id.di_poin * ratio
                        line.di_poib = move.sale_line_id.di_poib * ratio
                        line.di_nb_palette = ceil(move.sale_line_id.di_nb_palette * ratio)                
                        if move.di_un_saisie == "KG" or move.di_un_saisie == False:                    
                            line.di_qte_un_saisie = move.sale_line_id.di_qte_un_saisie * ratio
                        else:
                            line.di_qte_un_saisie = ceil(move.sale_line_id.di_qte_un_saisie * ratio)
                        line.di_tare = line.di_poib - line.di_poin
#                         if line.di_nb_colis != 0.0:
#                             line.di_tare_un = line.di_tare / ceil(line.di_nb_colis) 
                        if nbcol != 0.0:
                            line.di_tare_un = line.di_tare / ceil(nbcol)
                    else:
                        if move.purchase_line_id:
                            if  move.purchase_line_id.product_qty != 0.0:
                                ratio = line.product_qty / move.purchase_line_id.product_qty
                            else:
                                ratio = 1
                            line.di_nb_pieces = ceil(move.purchase_line_id.di_nb_pieces * ratio)
                            line.di_nb_colis = round(move.purchase_line_id.di_nb_colis * ratio,1)
                            nbcol = round(line.di_nb_colis,1)
                            line.di_poin = move.purchase_line_id.di_poin * ratio
                            line.di_poib = move.purchase_line_id.di_poib * ratio
                            line.di_nb_palette = ceil(move.purchase_line_id.di_nb_palette * ratio)                
                            if move.di_un_saisie == "KG" or move.di_un_saisie == False:                    
                                line.di_qte_un_saisie = move.purchase_line_id.di_qte_un_saisie * ratio
                            else:
                                line.di_qte_un_saisie = ceil(move.purchase_line_id.di_qte_un_saisie * ratio)
                            line.di_tare = line.di_poib - line.di_poin
#                             if line.di_nb_colis != 0.0:
#                                 line.di_tare_un = line.di_tare / ceil(line.di_nb_colis) 
                            if nbcol != 0.0:
                                line.di_tare_un = line.di_tare / ceil(nbcol)

                    
    @api.depends('move_line_ids.di_qte_un_saisie', 'move_line_ids.di_poin', 'move_line_ids.di_poib', 'move_line_ids.di_tare', 'move_line_ids.di_nb_colis', 'move_line_ids.di_nb_pieces', 'move_line_ids.di_nb_palette')
    def _compute_quantites(self):
        # recalcule la quantité en unité de saisie en fonction des ventils
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
                ref = self.env['di.ref.art.tiers'].search([('di_partner_id', '=', self.picking_partner_id.id), ('di_product_id', '=', self.product_id.id)], limit=1)
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
                        
    def write(self, vals):
        res = super(StockMove, self).write(vals)
        if 'product_uom_qty' in vals or 'di_nb_colis' in vals or 'di_qte_un_saisie' in vals or 'di_nb_pieces' in vals or 'di_nb_palette' in vals or 'di_poin' in vals or 'di_poib' in vals :
            self.filtered(lambda m: m.state == 'done' and m.purchase_line_id).mapped(
                'purchase_line_id').sudo()._update_received_qty()
        return res                        
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
                    # on attribue par défaut les valeurs de la ligne de commande   
                    vals["di_tare"] = Disaleorderline.di_tare   
                    vals["di_un_saisie"] = Disaleorderline.di_un_saisie
                    vals["di_type_palette_id"] = Disaleorderline.di_type_palette_id.id
                    vals["di_product_packaging_id"] = Disaleorderline.product_packaging.id                                                         
                    vals["di_flg_modif_uom"] = Disaleorderline.di_flg_modif_uom                    
        
        if vals.get('purchase_line_id'):    
            purchaseline = self.env['purchase.order.line'].search([('id', '=', vals["purchase_line_id"])], limit=1)            
            if purchaseline.id != False: 
                vals["di_tare"] = purchaseline.di_tare   
                vals["di_un_saisie"] = purchaseline.di_un_saisie
                vals["di_type_palette_id"] = purchaseline.di_type_palette_id.id
                vals["di_nb_pieces"] = purchaseline.di_nb_pieces - purchaseline.get_nb_pieces_enliv()
                vals["di_nb_colis"] = purchaseline.di_nb_colis - purchaseline.get_nb_colis_enliv()
                vals["di_poin"] = purchaseline.di_poin - purchaseline.get_poin_enliv()
                vals["di_poib"] = purchaseline.di_poib - purchaseline.get_poib_enliv()
                vals["di_nb_palette"] = purchaseline.di_nb_palette - purchaseline.get_nb_palette_enliv()
                vals["di_qte_un_saisie"] = purchaseline.di_qte_un_saisie - purchaseline.get_qte_un_saisie_enliv()
                vals["di_product_packaging_id"] = purchaseline.product_packaging.id
        res = super(StockMove, self).create(vals)
        if res.picking_type_id.code == 'incoming':  # 1: # 1 correspond à une réception, 5 à un envoi. Il y en a d'autres mais qui n'ont pas l'air de servir pour le moment.  
            # en création directe de BL, cela ne génère par de "ventilation". Je la génère pour pouvoir attribuer le lot en auto sur les achats
            if res.move_line_ids.id == False and  res.purchase_line_id.order_id.id == False:  # si on confirme une commande d'achat, la ligne est déjà créée
                vals = res._prepare_move_line_vals(quantity=res.product_qty - res.reserved_availability)
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
    
    def di_somme_quantites_montants(self, product_id,date_cr_cout_veille, date=False, cde_ach=False, dernier_id=0): # calcul cmp        
        qte = 0.0
        mont = 0.0
        nbcol = 0.0
        nbpal = 0.0
        nbpiece = 0.0
        poids = 0.0
        dernier_id_lu = 0
        dernier_cmp = 0
        
        query_args = {'di_product_id': product_id.id,'date':date}          
        query = """ select c.di_cmp 
                            from di_cout c                            
                            where cast(c.di_date as varchar)  <= cast(%(date)s as varchar) and di_product_id = %(di_product_id)s
                            order by di_date desc
                            limit 1                                                                                                                  
                        """    
                        
        self.env.cr.execute(query, query_args)
                                               
        try: 
            result = self.env.cr.fetchall()[0] 
            dernier_cmp = result[0] and result[0] or 0.0                         
        except:
            dernier_cout_di_qte = 0.0
            dernier_cout_di_mont = 0.0  
            query_args = {'di_product_id': product_id.id,'date':date}          
            query = """ select pol.price_subtotal,pol.product_uom_qty 
                            from purchase_order_line pol        
                            left join purchase_order po on po.id = pol.order_id                    
                            where cast(po.date_order as varchar)  <= cast(%(date)s as varchar) and pol.product_id = %(di_product_id)s and pol.price_unit > 0.0 and pol.product_uom_qty > 0.0
                            order by po.date_order desc
                            limit 1                                                                                                                  
                        """                                                
            self.env.cr.execute(query, query_args)            
            try: 
                result = self.env.cr.fetchall()[0] 
                achat_price_subtotal = result[0] and result[0] or 0.0
                achat_product_uom_qty = result[1] and result[1] or 0.0
                if achat_product_uom_qty != 0.0:
                    dernier_cmp = round((achat_price_subtotal / achat_product_uom_qty),2)
                else :
                    dernier_cmp=0                                                     
            except:
                achat_price_subtotal = 0.0
                achat_product_uom_qty = 0.0                                                      
                
        if dernier_cmp ==0.0:
            dernier_cmp= product_id.standard_price
        
        if cde_ach:
            if date:
                query = """ select sm.id,sm.purchase_line_id,sm.state,sm.di_nb_colis,sm.di_nb_palette,sm.di_nb_pieces,sm.di_poin,(select sum(sml.qty_done) from stock_move_line sml where sml.move_id = sm.id)as quantity_done,sm.product_uom_qty,sm.sale_line_id,pol.di_un_prix,pol.price_unit 
                            from stock_move sm
                            left join stock_location sl on sl.id = sm.location_dest_id
                            left join stock_picking sp on sp.id = sm.picking_id
                            left join purchase_order_line pol on pol.id = sm.purchase_line_id
                            where sm.state in ('done','assigned') and sm.picking_id is not null and sl.usage <> 'internal' 
                            and sm.product_id = %(product_id)s                            
                            and (
                                (sm.state='done' and left(cast(sp.date_done as varchar),10)< cast(%(date)s as varchar) and sm.id > %(dernier_id)s and cast(sp.date_done as varchar) > cast(%(date_cr_cout_veille)s as varchar) )
                                or (sm.state='assigned' and left(cast(sp.scheduled_date as varchar),10)< cast(%(date)s as varchar) and sm.id > %(dernier_id)s and cast(sp.scheduled_date as varchar) > cast(%(date_cr_cout_veille)s as varchar))                                
                            )     
                            order by case when sm.state='done' then sp.date_done else sp.scheduled_date end ,sm.id                                                                                                          
                        """
            else:
                query = """ select sm.id,sm.purchase_line_id,sm.state,sm.di_nb_colis,sm.di_nb_palette,sm.di_nb_pieces,sm.di_poin,(select sum(sml.qty_done) from stock_move_line sml where sml.move_id = sm.id)as quantity_done,sm.product_uom_qty,sm.sale_line_id,pol.di_un_prix,pol.price_unit
                            from stock_move sm
                            left join stock_location sl on sl.id = sm.location_dest_id
                            left join stock_picking sp on sp.id = sm.picking_id
                            left join purchase_order_line pol on pol.id = sm.purchase_line_id
                            where sm.state in ('done','assigned') and sm.picking_id is not null and sl.usage = 'internal'    
                            and sm.product_id = %(product_id)s     
                            order by case when sm.state='done' then sp.date_done else sp.scheduled_date end ,sm.id                                    
                        """
        else:
            if date:
                query = """ select sm.id,sm.purchase_line_id,sm.state,sm.di_nb_colis,sm.di_nb_palette,sm.di_nb_pieces,sm.di_poin,(select sum(sml.qty_done) from stock_move_line sml where sml.move_id = sm.id)as quantity_done,sm.product_uom_qty,sm.sale_line_id,pol.di_un_prix,pol.price_unit
                            from stock_move sm
                            left join stock_location sl on sl.id = sm.location_dest_id
                            left join stock_picking sp on sp.id = sm.picking_id
                            left join purchase_order_line pol on pol.id = sm.purchase_line_id
                            where sm.state in ('done') and sm.picking_id is not null and sl.usage <> 'internal' 
                            and sm.product_id = %(product_id)s                            
                            and (
                                (sm.state='done' and left(cast(sp.date_done as varchar),10)< cast(%(date)s as varchar) and sm.id > %(dernier_id)s and cast(sp.date_done as varchar) > cast(%(date_cr_cout_veille)s as varchar) )                               
                            )    
                            order by sp.date_done,sm.id                                                                                                           
                        """

            else:
                query = """ select sm.id,sm.purchase_line_id,sm.state,sm.di_nb_colis,sm.di_nb_palette,sm.di_nb_pieces,sm.di_poin,(select sum(sml.qty_done) from stock_move_line sml where sml.move_id = sm.id)as quantity_done,sm.product_uom_qty,sm.sale_line_id,pol.di_un_prix,pol.price_unit
                            from stock_move sm
                            left join stock_location sl on sl.id = sm.location_dest_id
                            left join stock_picking sp on sp.id = sm.picking_id
                            left join purchase_order_line pol on pol.id = sm.purchase_line_id
                            where sm.state in ('done') and sm.picking_id is not null and sl.usage <> 'internal' 
                            and sm.product_id = %(product_id)s  
                            order by sp.date_done,sm.id                                                                                                                                                                 
                        """                        
        query_args = {'product_id': product_id.id,'date' : date,'dernier_id' : dernier_id, 'date_cr_cout_veille': date_cr_cout_veille}        
 
        self.env.cr.execute(query, query_args)
        ids=[]
        for r in self.env.cr.fetchall():
            ids.append(r)

        for (mouv_id,mouv_purchase_line_id,mouv_state,mouv_di_nb_colis,mouv_di_nb_palette,mouv_di_nb_pieces,mouv_di_poin,mouv_quantity_done,mouv_product_uom_qty,mouv_sale_line_id,mouv_purchase_line_id_di_un_prix,mouv_purchase_line_id_price_unit) in ids: 
            if not mouv_di_nb_colis :
                mouv_di_nb_colis =0.0
            if not mouv_di_nb_palette :
                mouv_di_nb_palette =0.0
            if not mouv_di_nb_pieces :
                mouv_di_nb_pieces =0.0
            if not mouv_di_poin :
                mouv_di_poin =0.0
            if not mouv_quantity_done :
                mouv_quantity_done =0.0
            if not mouv_product_uom_qty :
                mouv_product_uom_qty =0.0
            if not mouv_purchase_line_id_price_unit :
                mouv_purchase_line_id_price_unit =0.0
                
            if mouv_id > dernier_id_lu:
                dernier_id_lu = mouv_id
            
            if mouv_purchase_line_id:
                if mouv_state == 'done':
                    nbcol = nbcol - mouv_di_nb_colis
                    nbpal = nbpal - mouv_di_nb_palette
                    nbpiece = nbpiece - mouv_di_nb_pieces
                    poids = poids - mouv_di_poin                
                    qte = qte -  mouv_quantity_done                                               
                else:
                    nbcol = nbcol - mouv_di_nb_colis
                    nbpal = nbpal - mouv_di_nb_palette
                    nbpiece = nbpiece - mouv_di_nb_pieces
                    poids = poids - mouv_di_poin                
                    qte = qte -  mouv_product_uom_qty 
                di_qte_prix = 0.0
                if mouv_purchase_line_id_di_un_prix == "PIECE":
                    if mouv_state == 'done':
                        di_qte_prix = mouv_di_nb_pieces
                    else:
                        di_qte_prix = mouv_di_nb_pieces                            
                elif mouv_purchase_line_id_di_un_prix == "COLIS":
                    if mouv_state == 'done':
                        di_qte_prix = mouv_di_nb_colis
                    else:
                        di_qte_prix = mouv_di_nb_colis
                elif mouv_purchase_line_id_di_un_prix == "PALETTE":
                    if mouv_state == 'done':
                        di_qte_prix = mouv_di_nb_palette
                    else:
                        di_qte_prix = mouv_di_nb_palette
                elif mouv_purchase_line_id_di_un_prix == "KG":
                    if mouv_state == 'done':
                        di_qte_prix = mouv_di_poin
                    else:
                        di_qte_prix = mouv_di_poin
                elif mouv_purchase_line_id_di_un_prix == False or mouv_purchase_line_id_di_un_prix == '':
                    if mouv_state == 'done':
                        di_qte_prix = mouv_quantity_done
                    else:
                        di_qte_prix = mouv_product_uom_qty
                mont = mont - (di_qte_prix * mouv_purchase_line_id_price_unit)    
            elif mouv_sale_line_id:
                if mouv_state == 'done':
                    nbcol = nbcol - mouv_di_nb_colis
                    nbpal = nbpal - mouv_di_nb_palette
                    nbpiece = nbpiece - mouv_di_nb_pieces
                    poids = poids - mouv_di_poin                
                    qte = qte -  mouv_quantity_done                        
                else:
                    nbcol = nbcol - mouv_di_nb_colis
                    nbpal = nbpal - mouv_di_nb_palette
                    nbpiece = nbpiece - mouv_di_nb_pieces
                    poids = poids - mouv_di_poin                
                    qte = qte -  mouv_product_uom_qty
                di_qte_prix = 0.0
                if mouv_state == 'done':
                    di_qte_prix = mouv_quantity_done
                else:
                    di_qte_prix = mouv_product_uom_qty
                mont = mont - (di_qte_prix * dernier_cmp)  
            else:                    
                nbcol = nbcol - mouv_di_nb_colis
                nbpal = nbpal - mouv_di_nb_palette
                nbpiece = nbpiece - mouv_di_nb_pieces
                poids = poids - mouv_di_poin                
                qte = qte -  mouv_quantity_done                                             
                di_qte_prix = 0.0                    
                di_qte_prix = mouv_quantity_done                                        
                mont = mont - (di_qte_prix * dernier_cmp)
        
        if cde_ach:
            if date:                                
                query = """ select sm.id,sm.purchase_line_id,sm.state,sm.di_nb_colis,sm.di_nb_palette,sm.di_nb_pieces,sm.di_poin,(select sum(sml.qty_done) from stock_move_line sml where sml.move_id = sm.id)as quantity_done,sm.product_uom_qty,sm.sale_line_id,pol.di_un_prix,pol.price_unit 
                            from stock_move sm
                            left join stock_location sl on sl.id = sm.location_dest_id
                            left join stock_picking sp on sp.id = sm.picking_id
                            left join purchase_order_line pol on pol.id = sm.purchase_line_id
                            where sm.state in ('done','assigned') and sm.picking_id is not null and sl.usage = 'internal' 
                            and sm.product_id = %(product_id)s                            
                            and (
                                (sm.state='done' and left(cast(sp.date_done as varchar),10)< cast(%(date)s as varchar) and sm.id > %(dernier_id)s and cast(sp.date_done as varchar) > cast(%(date_cr_cout_veille)s as varchar))
                                or (sm.state='done' and left(cast(sp.date_done as varchar),10)= cast(%(date)s as varchar) )
                                or (sm.state='assigned' and left(cast(sp.scheduled_date as varchar),10)< cast(%(date)s as varchar) and sm.id > %(dernier_id)s and cast(sp.scheduled_date as varchar) > cast(%(date_cr_cout_veille)s as varchar))
                                or (sm.state='assigned' and left(cast(sp.scheduled_date as varchar),10)= cast(%(date)s as varchar) )
                            )    
                            order by  case when sm.state='done' then sp.date_done else sp.scheduled_date end ,sm.id                                                                                                           
                        """
            else:
                query = """ select sm.id,sm.purchase_line_id,sm.state,sm.di_nb_colis,sm.di_nb_palette,sm.di_nb_pieces,sm.di_poin,(select sum(sml.qty_done) from stock_move_line sml where sml.move_id = sm.id)as quantity_done,sm.product_uom_qty,sm.sale_line_id,pol.di_un_prix,pol.price_unit 
                            from stock_move sm
                            left join stock_location sl on sl.id = sm.location_dest_id
                            left join stock_picking sp on sp.id = sm.picking_id
                            left join purchase_order_line pol on pol.id = sm.purchase_line_id
                            where sm.state in ('done','assigned') and sm.picking_id is not null and sl.usage = 'internal'    
                            and sm.product_id = %(product_id)s     
                            order by case when sm.state='done' then sp.date_done else sp.scheduled_date end ,sm.id                                    
                        """
        else:
            if date:
                query = """ select sm.id,sm.purchase_line_id,sm.state,sm.di_nb_colis,sm.di_nb_palette,sm.di_nb_pieces,sm.di_poin,(select sum(sml.qty_done) from stock_move_line sml where sml.move_id = sm.id)as quantity_done,sm.product_uom_qty,sm.sale_line_id,pol.di_un_prix,pol.price_unit 
                            from stock_move sm
                            left join stock_location sl on sl.id = sm.location_dest_id
                            left join stock_picking sp on sp.id = sm.picking_id
                            left join purchase_order_line pol on pol.id = sm.purchase_line_id
                            where sm.state in ('done') and sm.picking_id is not null and sl.usage = 'internal' 
                            and sm.product_id = %(product_id)s                            
                            and (
                                (sm.state='done' and left(cast(sp.date_done as varchar),10)< cast(%(date)s as varchar) and sm.id > %(dernier_id)s and cast(sp.date_done as varchar) > cast(%(date_cr_cout_veille)s as varchar))
                                or (sm.state='done' and left(cast(sp.date_done as varchar),10)= cast(%(date)s as varchar) )                               
                            )  
                            order by sp.date_done,sm.id                                                                                                             
                        """
            else:
                query = """ select sm.id,sm.purchase_line_id,sm.state,sm.di_nb_colis,sm.di_nb_palette,sm.di_nb_pieces,sm.di_poin,(select sum(sml.qty_done) from stock_move_line sml where sml.move_id = sm.id)as quantity_done,sm.product_uom_qty,sm.sale_line_id,pol.di_un_prix,pol.price_unit
                            from stock_move sm
                            left join stock_location sl on sl.id = sm.location_dest_id
                            left join stock_picking sp on sp.id = sm.picking_id
                            left join purchase_order_line pol on pol.id = sm.purchase_line_id
                            where sm.state in ('done') and sm.picking_id is not null and sl.usage = 'internal' 
                            and sm.product_id = %(product_id)s
                            order by sp.date_done,sm.id                                                                                                                                                                   
                        """
        
        
        query_args = {'product_id': product_id.id,'date' : date,'dernier_id' : dernier_id, 'date_cr_cout_veille': date_cr_cout_veille}        
 
        self.env.cr.execute(query, query_args)
        ids=[]
        for r in self.env.cr.fetchall():
            ids.append(r)

        for (mouv_id,mouv_purchase_line_id,mouv_state,mouv_di_nb_colis,mouv_di_nb_palette,mouv_di_nb_pieces,mouv_di_poin,mouv_quantity_done,mouv_product_uom_qty,mouv_sale_line_id,mouv_purchase_line_id_di_un_prix,mouv_purchase_line_id_price_unit) in ids: 
            if not mouv_di_nb_colis :
                mouv_di_nb_colis =0.0
            if not mouv_di_nb_palette :
                mouv_di_nb_palette =0.0
            if not mouv_di_nb_pieces :
                mouv_di_nb_pieces =0.0
            if not mouv_di_poin :
                mouv_di_poin =0.0
            if not mouv_quantity_done :
                mouv_quantity_done =0.0
            if not mouv_product_uom_qty :
                mouv_product_uom_qty =0.0
            if not mouv_purchase_line_id_price_unit :
                mouv_purchase_line_id_price_unit =0.0
                
            if mouv_id > dernier_id_lu:
                dernier_id_lu = mouv_id

            if mouv_purchase_line_id:

                if mouv_state == 'done':
                    nbcol = nbcol + mouv_di_nb_colis
                    nbpal = nbpal + mouv_di_nb_palette
                    nbpiece = nbpiece + mouv_di_nb_pieces
                    poids = poids + mouv_di_poin                
                    qte = qte +  mouv_quantity_done                     
                else:
                    nbcol = nbcol + mouv_di_nb_colis
                    nbpal = nbpal + mouv_di_nb_palette
                    nbpiece = nbpiece + mouv_di_nb_pieces
                    poids = poids + mouv_di_poin                
                    qte = qte +  mouv_product_uom_qty    
                di_qte_prix = 0.0
                if mouv_purchase_line_id_di_un_prix == "PIECE":
                    if mouv_state == 'done':
                        di_qte_prix = mouv_di_nb_pieces
                    else:
                        di_qte_prix = mouv_di_nb_pieces
                        
                elif mouv_purchase_line_id_di_un_prix == "COLIS":
                    if mouv_state == 'done':
                        di_qte_prix = mouv_di_nb_colis
                    else:
                        di_qte_prix = mouv_di_nb_colis
                elif mouv_purchase_line_id_di_un_prix == "PALETTE":
                    if mouv_state == 'done':
                        di_qte_prix = mouv_di_nb_palette
                    else:
                        di_qte_prix = mouv_di_nb_palette
                elif mouv_purchase_line_id_di_un_prix == "KG":
                    if mouv_state == 'done':
                        di_qte_prix = mouv_di_poin
                    else:
                        di_qte_prix = mouv_di_poin
                elif mouv_purchase_line_id_di_un_prix == False or mouv_purchase_line_id_di_un_prix == '':
                    if mouv_state == 'done':
                        di_qte_prix = mouv_quantity_done
                    else:
                        di_qte_prix = mouv_product_uom_qty                            
                
                mont = mont + (di_qte_prix * mouv_purchase_line_id_price_unit)
            elif mouv_sale_line_id:
                if mouv_state == 'done':
                    nbcol = nbcol + mouv_di_nb_colis
                    nbpal = nbpal + mouv_di_nb_palette
                    nbpiece = nbpiece + mouv_di_nb_pieces
                    poids = poids + mouv_di_poin                
                    qte = qte +  mouv_quantity_done                       
                else:
                    nbcol = nbcol + mouv_di_nb_colis
                    nbpal = nbpal + mouv_di_nb_palette
                    nbpiece = nbpiece + mouv_di_nb_pieces
                    poids = poids + mouv_di_poin                
                    qte = qte +  mouv_product_uom_qty
                di_qte_prix = 0.0
                if mouv_state == 'done':
                    di_qte_prix = mouv_quantity_done
                else:
                    di_qte_prix = mouv_product_uom_qty                        
                mont = mont + (di_qte_prix * product_id.di_get_dernier_cmp(date)) 
            else:                    
                nbcol = nbcol + mouv_di_nb_colis
                nbpal = nbpal + mouv_di_nb_palette
                nbpiece = nbpiece + mouv_di_nb_pieces
                poids = poids + mouv_di_poin                
                qte = qte +  mouv_quantity_done                                             
                di_qte_prix = 0.0                    
                di_qte_prix = mouv_quantity_done                                            
                mont = mont + (di_qte_prix * product_id.di_get_dernier_cmp(date)) 
                
                
        nouveau_cmp=0  
        query_args = {'di_product_id': product_id.id,'date':date}          
        query = """ select c.di_mont,c.di_qte 
                            from di_cout c                            
                            where cast(c.di_date as varchar)  <= cast(%(date)s as varchar) and di_product_id = %(di_product_id)s
                            order by di_date desc
                            limit 1                                                                                                                  
                        """    
                        
        self.env.cr.execute(query, query_args)
                                               
        try: 
            result = self.env.cr.fetchall()[0] 
            dernier_cout_di_mont = result[0] and result[0] or 0.0
            dernier_cout_di_qte = result[1] and result[1] or 0.0   
            if dernier_cout_di_qte + qte != 0.0:
                nouveau_cmp = round((dernier_cout_di_mont + mont) / (dernier_cout_di_qte + qte),2)
            else:
                nouveau_cmp=0             
        except:
            dernier_cout_di_qte = 0.0
            dernier_cout_di_mont = 0.0  
            query_args = {'di_product_id': product_id.id,'date':date}          
            query = """ select pol.price_subtotal,pol.product_uom_qty 
                            from purchase_order_line pol        
                            left join purchase_order po on po.id = pol.order_id                    
                            where cast(po.date_order as varchar)  <= cast(%(date)s as varchar) and pol.product_id = %(di_product_id)s and pol.price_unit > 0.0 and pol.product_uom_qty > 0.0
                            order by po.date_order desc
                            limit 1                                                                                                                  
                        """                                                
            self.env.cr.execute(query, query_args)            
            try: 
                result = self.env.cr.fetchall()[0] 
                achat_price_subtotal = result[0] and result[0] or 0.0
                achat_product_uom_qty = result[1] and result[1] or 0.0
                if achat_product_uom_qty != 0.0:
                    nouveau_cmp = round((achat_price_subtotal / achat_product_uom_qty),2)
                else :
                    nouveau_cmp=0                                                     
            except:
                achat_price_subtotal = 0.0
                achat_product_uom_qty = 0.0                                                      
                
        if nouveau_cmp ==0.0:
            nouveau_cmp= product_id.standard_price
                
#         #à optimiser  en sql              
#           
#         couts=self.env['di.cout'].search([('di_product_id', '=', product_id.id)]).filtered(lambda c: c.di_date<=date).sorted(key=lambda k: k.di_date,reverse=True)
#         dernier_cout=self.env['di.cout']
#         nouveau_cmp=0        
#         for cout in couts:
#             dernier_cout = cout
#             break
#         if not dernier_cout:
#             #à optimiser  en sql
#             achats=self.env['purchase.order.line'].search(['&',('product_id','=',product_id.id),('price_unit','>',0.0)]).filtered(lambda a: a.order_id.date_order.date()<=date).sorted(key=lambda k: k.order_id.date_order,reverse=True)
#             for achat in achats:
#                 if achat.product_uom_qty != 0.0:
#                     nouveau_cmp = round((achat.price_subtotal / achat.product_uom_qty),2)
#                     break
#             if nouveau_cmp ==0.0:
# #                 product=self.env['product.product'].browse(product_id)
#                 nouveau_cmp= product_id.standard_price
#         else:            
#             if dernier_cout.di_qte + qte != 0.0:
#                 nouveau_cmp = (dernier_cout.di_mont + mont) / (dernier_cout.di_qte + qte)
#             else:
#                 nouveau_cmp=0
                
        if cde_ach:
            if date:
                query = """ select sm.id,sm.purchase_line_id,sm.state,sm.di_nb_colis,sm.di_nb_palette,sm.di_nb_pieces,sm.di_poin,(select sum(sml.qty_done) from stock_move_line sml where sml.move_id = sm.id)as quantity_done,sm.product_uom_qty,sm.sale_line_id,pol.di_un_prix,pol.price_unit 
                            from stock_move sm
                            left join stock_location sl on sl.id = sm.location_dest_id
                            left join stock_picking sp on sp.id = sm.picking_id
                            left join purchase_order_line pol on pol.id = sm.purchase_line_id
                            where sm.state in ('done','assigned') and sm.picking_id is not null and sl.usage <> 'internal' 
                            and sm.product_id = %(product_id)s                            
                            and (
                                (sm.state='done' and left(cast(sp.date_done as varchar),10)= cast(%(date)s as varchar) )
                                or (sm.state='assigned' and left(cast(sp.scheduled_date as varchar),10)= cast(%(date)s as varchar) )
                            )     
                            order by case when sm.state='done' then sp.date_done else sp.scheduled_date end ,sm.id                                                                                                          
                        """
            else:
                query = """ select sm.id,sm.purchase_line_id,sm.state,sm.di_nb_colis,sm.di_nb_palette,sm.di_nb_pieces,sm.di_poin,(select sum(sml.qty_done) from stock_move_line sml where sml.move_id = sm.id)as quantity_done,sm.product_uom_qty,sm.sale_line_id,pol.di_un_prix,pol.price_unit
                            from stock_move sm
                            left join stock_location sl on sl.id = sm.location_dest_id
                            left join stock_picking sp on sp.id = sm.picking_id
                            left join purchase_order_line pol on pol.id = sm.purchase_line_id
                            where sm.state in ('done','assigned') and sm.picking_id is not null and sl.usage = 'internal'    
                            and sm.product_id = %(product_id)s     
                            order by case when sm.state='done' then sp.date_done else sp.scheduled_date end ,sm.id                                    
                        """
        else:
            if date:
                query = """ select sm.id,sm.purchase_line_id,sm.state,sm.di_nb_colis,sm.di_nb_palette,sm.di_nb_pieces,sm.di_poin,(select sum(sml.qty_done) from stock_move_line sml where sml.move_id = sm.id)as quantity_done,sm.product_uom_qty,sm.sale_line_id,pol.di_un_prix,pol.price_unit
                            from stock_move sm
                            left join stock_location sl on sl.id = sm.location_dest_id
                            left join stock_picking sp on sp.id = sm.picking_id
                            left join purchase_order_line pol on pol.id = sm.purchase_line_id
                            where sm.state in ('done') and sm.picking_id is not null and sl.usage <> 'internal' 
                            and sm.product_id = %(product_id)s                            
                            and (
                                (sm.state='done' and left(cast(sp.date_done as varchar),10)= cast(%(date)s as varchar) )                               
                            )    
                            order by sp.date_done,sm.id                                                                                                           
                        """

            else:
                query = """ select sm.id,sm.purchase_line_id,sm.state,sm.di_nb_colis,sm.di_nb_palette,sm.di_nb_pieces,sm.di_poin,(select sum(sml.qty_done) from stock_move_line sml where sml.move_id = sm.id)as quantity_done,sm.product_uom_qty,sm.sale_line_id,pol.di_un_prix,pol.price_unit
                            from stock_move sm
                            left join stock_location sl on sl.id = sm.location_dest_id
                            left join stock_picking sp on sp.id = sm.picking_id
                            left join purchase_order_line pol on pol.id = sm.purchase_line_id
                            where sm.state in ('done') and sm.picking_id is not null and sl.usage <> 'internal' 
                            and sm.product_id = %(product_id)s  
                            order by sp.date_done,sm.id                                                                                                                                                                 
                        """                        
        query_args = {'product_id': product_id.id,'date' : date,'dernier_id' : dernier_id, 'date_cr_cout_veille': date_cr_cout_veille}        
 
        self.env.cr.execute(query, query_args)
        ids=[]
        for r in self.env.cr.fetchall():
            ids.append(r)

        for (mouv_id,mouv_purchase_line_id,mouv_state,mouv_di_nb_colis,mouv_di_nb_palette,mouv_di_nb_pieces,mouv_di_poin,mouv_quantity_done,mouv_product_uom_qty,mouv_sale_line_id,mouv_purchase_line_id_di_un_prix,mouv_purchase_line_id_price_unit) in ids: 
            if not mouv_di_nb_colis :
                mouv_di_nb_colis =0.0
            if not mouv_di_nb_palette :
                mouv_di_nb_palette =0.0
            if not mouv_di_nb_pieces :
                mouv_di_nb_pieces =0.0
            if not mouv_di_poin :
                mouv_di_poin =0.0
            if not mouv_quantity_done :
                mouv_quantity_done =0.0
            if not mouv_product_uom_qty :
                mouv_product_uom_qty =0.0
            if not mouv_purchase_line_id_price_unit :
                mouv_purchase_line_id_price_unit =0.0
                
            if mouv_id > dernier_id_lu:
                dernier_id_lu = mouv_id
            
            if mouv_purchase_line_id:
                if mouv_state == 'done':
                    nbcol = nbcol - mouv_di_nb_colis
                    nbpal = nbpal - mouv_di_nb_palette
                    nbpiece = nbpiece - mouv_di_nb_pieces
                    poids = poids - mouv_di_poin                
                    qte = qte -  mouv_quantity_done                                               
                else:
                    nbcol = nbcol - mouv_di_nb_colis
                    nbpal = nbpal - mouv_di_nb_palette
                    nbpiece = nbpiece - mouv_di_nb_pieces
                    poids = poids - mouv_di_poin                
                    qte = qte -  mouv_product_uom_qty 
                di_qte_prix = 0.0
                if mouv_purchase_line_id_di_un_prix == "PIECE":
                    if mouv_state == 'done':
                        di_qte_prix = mouv_di_nb_pieces
                    else:
                        di_qte_prix = mouv_di_nb_pieces                            
                elif mouv_purchase_line_id_di_un_prix == "COLIS":
                    if mouv_state == 'done':
                        di_qte_prix = mouv_di_nb_colis
                    else:
                        di_qte_prix = mouv_di_nb_colis
                elif mouv_purchase_line_id_di_un_prix == "PALETTE":
                    if mouv_state == 'done':
                        di_qte_prix = mouv_di_nb_palette
                    else:
                        di_qte_prix = mouv_di_nb_palette
                elif mouv_purchase_line_id_di_un_prix == "KG":
                    if mouv_state == 'done':
                        di_qte_prix = mouv_di_poin
                    else:
                        di_qte_prix = mouv_di_poin
                elif mouv_purchase_line_id_di_un_prix == False or mouv_purchase_line_id_di_un_prix == '':
                    if mouv_state == 'done':
                        di_qte_prix = mouv_quantity_done
                    else:
                        di_qte_prix = mouv_product_uom_qty
                mont = mont - (di_qte_prix * mouv_purchase_line_id_price_unit)    
            elif mouv_sale_line_id:
                if mouv_state == 'done':
                    nbcol = nbcol - mouv_di_nb_colis
                    nbpal = nbpal - mouv_di_nb_palette
                    nbpiece = nbpiece - mouv_di_nb_pieces
                    poids = poids - mouv_di_poin                
                    qte = qte -  mouv_quantity_done                        
                else:
                    nbcol = nbcol - mouv_di_nb_colis
                    nbpal = nbpal - mouv_di_nb_palette
                    nbpiece = nbpiece - mouv_di_nb_pieces
                    poids = poids - mouv_di_poin                
                    qte = qte -  mouv_product_uom_qty
                di_qte_prix = 0.0
                if mouv_state == 'done':
                    di_qte_prix = mouv_quantity_done
                else:
                    di_qte_prix = mouv_product_uom_qty
                mont = mont - (di_qte_prix * nouveau_cmp)  
            else:                    
                nbcol = nbcol - mouv_di_nb_colis
                nbpal = nbpal - mouv_di_nb_palette
                nbpiece = nbpiece - mouv_di_nb_pieces
                poids = poids - mouv_di_poin                
                qte = qte -  mouv_quantity_done                                             
                di_qte_prix = 0.0                    
                di_qte_prix = mouv_quantity_done                                        
                mont = mont - (di_qte_prix * nouveau_cmp)   


        if date:
            query = """ select sm.id,sm.state,sm.di_nb_colis,sm.di_nb_palette,sm.di_nb_pieces,sm.di_poin,(select sum(sml.qty_done) from stock_move_line sml where sml.move_id = sm.id)as quantity_done,sl.usage
                            from stock_move sm              
                            left join stock_location sl on sl.id = sm.location_dest_id                                      
                            where sm.state in ('done') and sm.picking_id is null  
                            and sm.product_id = %(product_id)s                            
                            and (
                                (left(cast(sm.date as varchar),10)< cast(%(date)s as varchar) and sm.id > %(dernier_id)s and cast(sm.date as varchar) > cast(%(date_cr_cout_veille)s as varchar) )
                                or (left(cast(sm.date as varchar),10)= cast(%(date)s as varchar) )                               
                            )  
                            order by sm.date,sm.id                                                                                                             
                        """
        else:
            query = """ select sm.id,sm.state,sm.di_nb_colis,sm.di_nb_palette,sm.di_nb_pieces,sm.di_poin,(select sum(sml.qty_done) from stock_move_line sml where sml.move_id = sm.id)as quantity_done,sl.usage
                            from stock_move sm               
                            left join stock_location sl on sl.id = sm.location_dest_id                                      
                            where sm.state in ('done') and sm.picking_id is null  
                            and sm.product_id = %(product_id)s                            
                            and (
                                ( sm.id > %(dernier_id)s and cast(sm.date as varchar) > cast(%(date_cr_cout_veille)s as varchar) )                                                            
                            )    
                            order by sm.date,sm.id                                                                                                           
                        """
            
        query_args = {'product_id': product_id.id,'date' : date,'dernier_id' : dernier_id, 'date_cr_cout_veille': date_cr_cout_veille}        
 
        self.env.cr.execute(query, query_args)
        ids=[]
        for r in self.env.cr.fetchall():
            ids.append(r)

        for (mouv_id,mouv_state,mouv_di_nb_colis,mouv_di_nb_palette,mouv_di_nb_pieces,mouv_di_poin,mouv_quantity_done,mouv_location_dest_id_usage) in ids: 
            if not mouv_di_nb_colis :
                mouv_di_nb_colis =0.0
            if not mouv_di_nb_palette :
                mouv_di_nb_palette =0.0
            if not mouv_di_nb_pieces :
                mouv_di_nb_pieces =0.0
            if not mouv_di_poin :
                mouv_di_poin =0.0
            if not mouv_quantity_done :
                mouv_quantity_done =0.0
           

            if mouv_id > dernier_id_lu:
                dernier_id_lu = mouv_id
            if mouv_quantity_done and mouv_quantity_done not in  (0.0,None,False):
                if mouv_location_dest_id_usage == 'internal':
                    qte = qte + mouv_quantity_done
                    nbcol = nbcol + mouv_di_nb_colis
                    nbpal = nbpal + mouv_di_nb_palette
                    nbpiece = nbpiece + mouv_di_nb_pieces
                    poids = poids + mouv_di_poin
                    mont = mont + (mouv_quantity_done * nouveau_cmp)
                else:
                    qte = qte - mouv_quantity_done 
                    nbcol = nbcol - mouv_di_nb_colis
                    nbpal = nbpal - mouv_di_nb_palette
                    nbpiece = nbpiece - mouv_di_nb_pieces
                    poids = poids - mouv_di_poin  
                    mont = mont - (mouv_quantity_done * nouveau_cmp) 
        mont  = round(mont,2)
        return (qte, mont, nbcol, nbpal, nbpiece, poids,dernier_id_lu,nouveau_cmp)
    
    @api.model
    def _run_fifo(self, move, quantity=None):   
        """ Value `move` according to the FIFO rule, meaning we consume the
        oldest receipt first. Candidates receipts are marked consumed or free
        thanks to their `remaining_qty` and `remaining_value` fields.
        By definition, `move` should be an outgoing stock move.

        :param quantity: quantity to value instead of `move.product_qty`
        :returns: valued amount in absolute
        """
#         reprise du standard car division par 0 sur calcul 'price_unit': -tmp_value / (move.product_qty or quantity),
        move.ensure_one()

        # Deal with possible move lines that do not impact the valuation.
        valued_move_lines = move.move_line_ids.filtered(lambda ml: ml.location_id._should_be_valued() and not ml.location_dest_id._should_be_valued() and not ml.owner_id)
        valued_quantity = 0
        for valued_move_line in valued_move_lines:
            valued_quantity += valued_move_line.product_uom_id._compute_quantity(valued_move_line.qty_done, move.product_id.uom_id)

        # Find back incoming stock moves (called candidates here) to value this move.
        qty_to_take_on_candidates = quantity or valued_quantity
        candidates = move.product_id._get_fifo_candidates_in_move_with_company(move.company_id.id)
        new_standard_price = 0
        tmp_value = 0  # to accumulate the value taken on the candidates
        for candidate in candidates:
            new_standard_price = candidate.price_unit
            if candidate.remaining_qty <= qty_to_take_on_candidates:
                qty_taken_on_candidate = candidate.remaining_qty
            else:
                qty_taken_on_candidate = qty_to_take_on_candidates

            # As applying a landed cost do not update the unit price, naivelly doing
            # something like qty_taken_on_candidate * candidate.price_unit won't make
            # the additional value brought by the landed cost go away.
            candidate_price_unit = candidate.remaining_value / candidate.remaining_qty
            value_taken_on_candidate = qty_taken_on_candidate * candidate_price_unit
            candidate_vals = {
                'remaining_qty': candidate.remaining_qty - qty_taken_on_candidate,
                'remaining_value': candidate.remaining_value - value_taken_on_candidate,
            }
            candidate.write(candidate_vals)

            qty_to_take_on_candidates -= qty_taken_on_candidate
            tmp_value += value_taken_on_candidate
            if qty_to_take_on_candidates == 0:
                break

        # Update the standard price with the price of the last used candidate, if any.
        if new_standard_price and move.product_id.cost_method == 'fifo':
            move.product_id.sudo().with_context(force_company=move.company_id.id) \
                .standard_price = new_standard_price

        # If there's still quantity to value but we're out of candidates, we fall in the
        # negative stock use case. We chose to value the out move at the price of the
        # last out and a correction entry will be made once `_fifo_vacuum` is called.
        if qty_to_take_on_candidates == 0:
            # début modif difodoo
            if move.product_qty==0.0 and not quantity:
                last_fifo_price = new_standard_price or move.product_id.standard_price
                di_price_unit = -1 * last_fifo_price
            else:
                di_price_unit = -tmp_value / (move.product_qty or quantity)
            # fin modif difodoo
            move.write({
                'value': -tmp_value if not quantity else move.value or -tmp_value,  # outgoing move are valued negatively
                #'price_unit': -tmp_value / (move.product_qty or quantity),
                'price_unit': di_price_unit,
            })
        elif qty_to_take_on_candidates > 0:
            last_fifo_price = new_standard_price or move.product_id.standard_price
            negative_stock_value = last_fifo_price * -qty_to_take_on_candidates
            tmp_value += abs(negative_stock_value)
            vals = {
                'remaining_qty': move.remaining_qty + -qty_to_take_on_candidates,
                'remaining_value': move.remaining_value + negative_stock_value,
                'value': -tmp_value,
                'price_unit': -1 * last_fifo_price,
            }
            move.write(vals)
        return tmp_value
                 
class StockMoveLine(models.Model):
    _inherit = "stock.move.line"
      
    di_qte_un_saisie = fields.Float(string='Quantité en unité de saisie', store=True, compute="_compute_qte_un_saisie")          
    di_nb_pieces = fields.Integer(string='Nb pièces', store=True)
    di_nb_colis = fields.Float(string='Nb colis' , store=True, digits=(8,1))
    di_nb_palette = fields.Float(string='Nb palettes', store=True, digits=dp.get_precision('Product Unit of Measure'))
    di_poin = fields.Float(string='Poids net' , store=True)
    di_poib = fields.Float(string='Poids brut', store=True)
    di_tare = fields.Float(string='Tare', store=True)  # ,compute="_compute_tare")    
    di_flg_modif_uom = fields.Boolean(default=False)
    di_flg_modif_qty_spe = fields.Boolean(default=False)
    di_flg_cloture = fields.Boolean(default=False)
    di_usage_loc = fields.Selection(related='location_id.usage', store=True)    
    di_usage_loc_dest = fields.Selection(related='location_dest_id.usage', store=True)
    di_lot_fini = fields.Boolean(related='lot_id.di_fini', store=True)
    
    di_spe_saisissable = fields.Boolean(string='Champs spé saisissables', default=False, compute='_di_compute_spe_saisissable', store=True)
#     di_partner_id = fields.Many2one(related="move_id.picking_id.partner_id" , string="Tiers",store=True)
    di_partner = fields.Many2one(related="move_id.picking_id.partner_id" , string="Tiers",store=True)
#     di_entree_sortie = fields.Char(string="Entrée / Sortie",  compute='_di_compute_entree_sortie', store=True)
    di_entrees_sorties = fields.Char(string="Entrée / Sortie",  compute='_di_compute_entree_sortie', store=True)
#     di_calc_es = fields.Boolean(string="Calc ES",  compute='_di_compute_es')
    di_prix = fields.Float(string='Prix', digits=dp.get_precision('Product Unit of Measure'),compute='_di_compute_valo')
    di_un_prix      = fields.Selection([("PIECE", "Pièce"), ("COLIS", "Colis"),("PALETTE", "Palette"),("KG","Kg")], string="Unité de prix",compute='_di_compute_valo')    
    di_valo = fields.Float(string='Valorisation', digits=dp.get_precision('Product Unit of Measure'),compute='_di_compute_valo')
            
    di_tare_un      = fields.Float(string='Tare unitaire')
    di_perte = fields.Boolean("Perte", default=False)
    
    di_valo_sign = fields.Float(string='Valorisation', digits=dp.get_precision('Product Unit of Measure'),compute='_di_compute_valo_sign')
    di_nb_pieces_sign = fields.Integer(string='Nb pièces',compute='_di_compute_sign', store=True)
    di_nb_colis_sign = fields.Float(string='Nb colis' ,compute='_di_compute_sign', store=True, digits=(8,1))
    di_nb_palette_sign = fields.Float(string='Nb palettes',compute='_di_compute_sign', digits=dp.get_precision('Product Unit of Measure'), store=True)
    di_poin_sign = fields.Float(string='Poids net' ,compute='_di_compute_sign', store=True)
    di_poib_sign = fields.Float(string='Poids brut',compute='_di_compute_sign', store=True)
    di_tare_sign = fields.Float(string='Tare',compute='_di_compute_sign', store=True)
    di_qty_done_sign = fields.Float('Quantité traitée', digits=dp.get_precision('Product Unit of Measure'), compute='_di_compute_sign', store=True)
    di_date_date = fields.Date('Date sans heure', compute='_di_comoute_date_date', store=True)
    
    
    
#     @api.model
#     def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
#         """
#             Inherit read_group to calculate the sum of the non-stored fields, as it is not automatically done anymore through the XML.
#         """
#         res = super(StockMoveLine, self).read_group(domain, fields, groupby, offset=offset, limit=limit, orderby=orderby, lazy=lazy)
#         fields_list = ['di_valo', 'di_valo_sign', 'di_nb_pieces_sign', 'di_nb_colis_sign', 'di_nb_palette_sign',
#                        'di_poin_sign', 'di_poib_sign', 'di_tare_sign', 'di_qty_done_sign']
#              
#         if any(x in fields for x in fields_list):
# #             for re in res:
# #                 re._di_compute_sign(field_names=[x for x in fields if fields in fields_list])
# #             # Calculate first for every stock move line in which line it needs to be applied
#             re_ind = 0
#             sml_re = {}
#             tot_sml = self.browse([])
#             for re in res:
#                 if re.get('__domain'):
#                     sml = self.search(re['__domain'])
#                     tot_sml |= sml
#                     for lig in sml:
#                         sml_re[lig.id] = re_ind
#                 re_ind += 1
#             res_val = tot_sml._di_compute_sign(field_names=[x for x in fields if fields in fields_list])
#             for key in res_val:
#                 for l in res_val[key]:
#                     re = res[sml_re[key]]
#                     if re.get(l):
#                         re[l] += res_val[key][l]
#                     else:
#                         re[l] = res_val[key][l]
#         return res
#     
#     @api.multi
#     def _di_compute_sign(self, field_names=None):
#         res = {}
#         if field_names is None:
#             field_names = []
#         for sml in self:
#             res[sml.id] = {}
#             di_valo = 0.0
#             if sml.move_id.purchase_line_id:
#                 sml.di_prix = sml.move_id.purchase_line_id.price_unit
#                 sml.di_un_prix = sml.move_id.purchase_line_id.di_un_prix
#             elif sml.move_id.sale_line_id:
#                 sml.di_prix = sml.move_id.sale_line_id.price_unit
#                 sml.di_un_prix = sml.move_id.sale_line_id.di_un_prix
#             else:
#                 sml.di_prix = sml.product_id.di_get_dernier_cmp(sml.date.date())
#                 sml.di_un_prix = False
#             if sml.di_un_prix:
#                 if sml.di_un_prix == 'PIECE':
#                     di_valo = sml.di_prix * sml.di_nb_pieces
#                 elif sml.di_un_prix == 'COLIS':
#                     di_valo = sml.di_prix * sml.di_nb_colis
#                 elif sml.di_un_prix == 'PALETTE':
#                     di_valo = sml.di_prix * sml.di_nb_palette
#                 elif sml.di_un_prix == 'KG':
#                     di_valo = sml.di_prix * sml.di_poin
#             else:
#                 if sml.state == 'done':
#                     di_valo = sml.di_prix * sml.qty_done
#                 else:
#                     di_valo = sml.di_prix * sml.product_uom_qty  
#                     
#             res[sml.id]['di_valo']=di_valo
#             if sml.di_entrees_sorties == 'entree': 
#                 res[sml.id]['di_valo_sign'] = res[sml.id]['di_valo']
#                 res[sml.id]['di_nb_pieces_sign'] = sml.di_nb_pieces
#                 res[sml.id]['di_nb_colis_sign'] = sml.di_nb_colis
#                 res[sml.id]['di_nb_palette_sign'] = sml.di_nb_palette
#                 res[sml.id]['di_poin_sign'] = sml.di_poin
#                 res[sml.id]['di_poib_sign'] = sml.di_poib
#                 res[sml.id]['di_tare_sign'] = sml.di_tare
#                 res[sml.id]['di_qty_done_sign'] = sml.qty_done                
#             else:  
#                 res[sml.id]['di_valo_sign'] = -res[sml.id]['di_valo']
#                 res[sml.id]['di_nb_pieces_sign'] = -sml.di_nb_pieces
#                 res[sml.id]['di_nb_colis_sign'] = -sml.di_nb_colis
#                 res[sml.id]['di_nb_palette_sign'] = -sml.di_nb_palette
#                 res[sml.id]['di_poin_sign'] = -sml.di_poin
#                 res[sml.id]['di_poib_sign'] = -sml.di_poib
#                 res[sml.id]['di_tare_sign'] = -sml.di_tare
#                 res[sml.id]['di_qty_done_sign'] = -sml.qty_done  
#             for k, v in res[sml.id].items():
#                 setattr(sml, k, v)
#         return res
    
    @api.multi
    @api.depends('date')
    def _di_comoute_date_date(self):        
        for sml in self:   
            sml.di_date_date = sml.date.date() 
    
    
    @api.multi
    @api.depends('di_entrees_sorties','di_nb_pieces','di_nb_colis','di_nb_palette','di_poin','di_poib','di_tare','qty_done')
    def _di_compute_sign(self):        
        for sml in self:                      
            if sml.di_entrees_sorties == 'entree': 
#                 sml.di_valo_sign = sml.di_valo
                sml.di_nb_pieces_sign = sml.di_nb_pieces
                sml.di_nb_colis_sign = sml.di_nb_colis
                sml.di_nb_palette_sign = sml.di_nb_palette
                sml.di_poin_sign = sml.di_poin
                sml.di_poib_sign = sml.di_poib
                sml.di_tare_sign = sml.di_tare
                sml.di_qty_done_sign = sml.qty_done                
            else:  
#                 sml.di_valo_sign = -sml.di_valo
                sml.di_nb_pieces_sign = -sml.di_nb_pieces
                sml.di_nb_colis_sign = -sml.di_nb_colis
                sml.di_nb_palette_sign = -sml.di_nb_palette
                sml.di_poin_sign = -sml.di_poin
                sml.di_poib_sign = -sml.di_poib
                sml.di_tare_sign = -sml.di_tare
                sml.di_qty_done_sign = -sml.qty_done  
         
         
    @api.multi
#     @api.depends('di_entrees_sorties','di_nb_pieces','di_nb_colis','di_nb_palette','di_poin','di_poib','di_tare','qty_done')
    def _di_compute_valo_sign(self):        
        for sml in self:                      
            if sml.di_entrees_sorties == 'entree': 
                sml.di_valo_sign = sml.di_valo                        
            else:  
                sml.di_valo_sign = -sml.di_valo             
    @api.multi
#     @api.depends('move_id','product_id')
    def _di_compute_valo(self):
        for sml in self:
            if sml.move_id.purchase_line_id:
#                 pol = self.env['purchase.order.line'].browse(sml.move_id.purchase_line_id.id) # les champs spé ne sont pas dispo sinon ??? bug? je ne comprends pas
#                 sml.di_prix = pol.price_unit
#                 sml.di_un_prix = pol.di_un_prix
#                 sml
#                 sml.di_prix = sml.move_id.purchase_line_id.price_unit
#                 sml.di_un_prix = sml.move_id.purchase_line_id.di_un_prix
                sqlstr = """
                    select
                        pol.price_unit,
                        pol.di_un_prix                                                                                                                       
                    from purchase_order_line pol                                                                            
                    where pol.id = %s 
                    """
                    
                self.env.cr.execute(sqlstr, (sml.move_id.purchase_line_id.id,))
                
                
                result = self.env.cr.fetchall()[0]
                sml.di_prix = result[0] and result[0] or 0.0
                sml.di_un_prix = result[1] and result[1] or False

            elif sml.move_id.sale_line_id:
                sml.di_prix = sml.move_id.sale_line_id.price_unit
                sml.di_un_prix = sml.move_id.sale_line_id.di_un_prix
            else:
                sml.di_prix = sml.product_id.di_get_dernier_cmp(sml.date.date())
                sml.di_un_prix = False
            if sml.di_un_prix:
                if sml.di_un_prix == 'PIECE':
                    sml.di_valo = sml.di_prix * sml.di_nb_pieces
                elif sml.di_un_prix == 'COLIS':
                    sml.di_valo = sml.di_prix * sml.di_nb_colis
                elif sml.di_un_prix == 'PALETTE':
                    sml.di_valo = sml.di_prix * sml.di_nb_palette
                elif sml.di_un_prix == 'KG':
                    sml.di_valo = sml.di_prix * sml.di_poin
            else:
                if sml.state == 'done':
                    sml.di_valo = sml.di_prix * sml.qty_done
                else:
                    sml.di_valo = sml.di_prix * sml.product_uom_qty  
      
    @api.multi
    @api.depends('di_usage_loc_dest')
    def _di_compute_entree_sortie(self):   
        for sml in self:
            if sml.di_usage_loc_dest=='internal':
                sml.di_entrees_sorties = 'entree'
            else:
                sml.di_entrees_sorties = 'sortie'            
            
    @api.multi
    @api.depends('product_id.di_spe_saisissable')
    def _di_compute_spe_saisissable(self):   
        for sml in self:     
            sml.di_spe_saisissable = sml.product_id.di_spe_saisissable
        
    @api.multi    
    @api.depends('di_poin', 'di_tare', 'di_nb_colis', 'di_nb_pieces', 'di_nb_palette')
    def _compute_qte_un_saisie(self):
        # recalcule la quantité en unité de saisie
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
            if self.di_flg_modif_uom == False:
                self.di_flg_modif_qty_spe = True   
                if self._context.get('di_move_id'):
                    move = self.env['stock.move'].browse(self._context['di_move_id'])
                else:
                    move = self.move_id                                       
                if move.di_type_palette_id:
                    self.di_nb_colis = round(self.di_nb_palette * move.di_type_palette_id.di_qte_cond_inf,1)  
                    nbcol = round(self.di_nb_colis,1)                
                    if move.product_uom.name.lower() == 'kg':       
#                         self.qty_done = move.di_product_packaging_id.qty * self.di_nb_colis * self.product_id.weight
                        self.qty_done = move.di_product_packaging_id.qty * nbcol * self.product_id.weight
                        self.di_poin = self.qty_done 
                    else:                                  
#                         self.qty_done = move.di_product_packaging_id.qty * self.di_nb_colis
                        self.qty_done = move.di_product_packaging_id.qty * nbcol
                        self.di_poin = self.qty_done  * self.product_id.weight
#                     self.di_nb_pieces = ceil(move.di_product_packaging_id.di_qte_cond_inf * self.di_nb_colis)
                    self.di_nb_pieces = ceil(move.di_product_packaging_id.di_qte_cond_inf * nbcol)            
                     
                    self.di_poib = self.di_poin + self.di_tare
      
    @api.multi                     
    @api.onchange('di_nb_colis')
    def _di_change_nb_colis(self):
        if self.ensure_one()and not self.move_id.inventory_id:
            if self.di_flg_modif_uom == False:
                self.di_flg_modif_qty_spe = True      
                self.di_tare_un = 0.0
                self.di_tare = 0.0
                if self._context.get('di_move_id'):
                    move = self.env['stock.move'].browse(self._context['di_move_id'])
                else:
                    move = self.move_id     
                if move.di_product_packaging_id: 
                    nbcol = round(self.di_nb_colis,1)
                    if move.product_uom.name.lower() == 'kg':       
#                         self.qty_done = move.di_product_packaging_id.qty * self.di_nb_colis * self.product_id.weight
                        self.qty_done = move.di_product_packaging_id.qty * nbcol * self.product_id.weight
                        self.di_poin = self.qty_done  
                    else:                                  
#                         self.qty_done = move.di_product_packaging_id.qty * self.di_nb_colis
                        self.qty_done = move.di_product_packaging_id.qty * nbcol
                        self.di_poin = self.qty_done  * self.product_id.weight
                          
#                     self.di_nb_pieces = ceil(move.di_product_packaging_id.di_qte_cond_inf * self.di_nb_colis)
                    self.di_nb_pieces = ceil(move.di_product_packaging_id.di_qte_cond_inf * nbcol)
                    if move.di_type_palette_id.di_qte_cond_inf != 0.0:                
#                         self.di_nb_palette = self.di_nb_colis / move.di_type_palette_id.di_qte_cond_inf
                        self.di_nb_palette = nbcol / move.di_type_palette_id.di_qte_cond_inf
                    else:
#                         self.di_nb_palette = self.di_nb_colis
                        self.di_nb_palette =nbcol
                    
                    self.di_poib = self.di_poin + self.di_tare
                
    @api.multi    
    @api.onchange('di_nb_colis', 'di_tare_un')
    def _di_recalcule_tare(self):
        if self.ensure_one():
            nbcol = round(self.di_nb_colis,1)
#             self.di_tare = self.di_tare_un * ceil(self.di_nb_colis)
            self.di_tare = self.di_tare_un * ceil(nbcol)
                
    @api.multi                     
    @api.onchange('di_nb_pieces')
    def _di_change_nb_pieces(self):
        if self.ensure_one()and not self.move_id.inventory_id:
            if self.di_flg_modif_uom == False:
                self.di_flg_modif_qty_spe = True      
                if self._context.get('di_move_id'):
                    move = self.env['stock.move'].browse(self._context['di_move_id'])
                else:
                    move = self.move_id
                if move.product_uom.name.lower() == 'kg':       
                    self.qty_done = self.di_nb_pieces * self.product_id.weight 
                    self.di_poin = self.qty_done  
                else:                                             
                    self.qty_done =self.di_nb_pieces
                    self.di_poin = self.qty_done  * self.product_id.weight
                self.di_poib = self.di_poin + self.di_tare

    @api.multi 
    @api.onchange('di_poib')
    def _di_onchange_poib(self):
        if self.ensure_one()and not self.move_id.inventory_id:
            if self.di_flg_modif_uom == False:
                self.di_flg_modif_qty_spe = True
                self.di_poin = self.di_poib - self.di_tare
                if self._context.get('di_move_id'):
                    move = self.env['stock.move'].browse(self._context['di_move_id'])
                else:
                    move = self.move_id                 
                if move.product_uom.name.lower() == 'kg':
                    self.qty_done = self.di_poin
   
    @api.multi 
    @api.onchange('di_tare')
    def _di_onchange_tare(self):
        if self.ensure_one()and not self.move_id.inventory_id:
            if self.di_flg_modif_uom == False:
                self.di_flg_modif_qty_spe = True    
                self.di_poin = self.di_poib - self.di_tare  
                if self._context.get('di_move_id'):
                    move = self.env['stock.move'].browse(self._context['di_move_id'])
                else:
                    move = self.move_id         
                if move.product_uom.name.lower() == 'kg':
                    self.qty_done = self.di_poin
                    
    @api.multi 
    @api.onchange('di_poin')
    def _di_onchange_poin(self):
        if self.ensure_one() and not self.move_id.inventory_id: 
            if self.di_flg_modif_uom == False:
                self.di_flg_modif_qty_spe = True     
                if self._context.get('di_move_id'):
                    move = self.env['stock.move'].browse(self._context['di_move_id'])
                else:
                    move = self.move_id                         
                if move.product_uom.name.lower() == 'kg':
                    self.qty_done = self.di_poin               
                self.di_poib = self.di_poin + self.di_tare
    
    @api.multi                     
    @api.onchange('qty_done')
    def _di_change_qty_done(self):
        if self.ensure_one() and not self.move_id.inventory_id:
            if self._context.get('di_move_id'):
                move = self.env['stock.move'].browse(self._context['di_move_id'])
            else:
                move = self.move_id                
            if self.di_flg_modif_qty_spe == False:
                if move.product_uom:
                    if move.product_uom.name.lower == 'kg':
                        # si géré au kg, on ne modife que les champs poids
                        self.di_poin = self.qty_done
                        self.di_poib = self.di_poin + self.di_tare
                        
                    if move.product_uom.name == 'Unit(s)' or move.product_uom.name == 'Pièce' :
                        self.di_nb_pieces = ceil(self.qty_done)
                    if move.product_uom.name.lower() ==  'colis' :
                        self.di_nb_colis = round(self.qty_done,1)
                    if move.product_uom.name.lower() ==  'palette' :
                        self.di_nb_palette = ceil(self.qty_done)
                                                
                    self.di_flg_modif_uom = True
            self.di_flg_modif_qty_spe=False
            
    @api.model
    def create(self, vals):        
        orig = self.env['stock.location'].browse(vals.get('location_id'))        
        if vals.get('picking_id') and orig.usage != 'customer' :
            if vals['picking_id'] != False:                  
                picking = self.env['stock.picking'].browse(vals['picking_id'])
                if picking.picking_type_id.code == 'incoming': 
                                       
                    if not vals.get('lot_id'):  # si pas de lot saisi
                        if vals.get('move_id') :  # si on a une commande liée
                            if vals['move_id'] != False:            
                                move = self.env['stock.move'].browse(vals['move_id'])
                                vals["di_nb_pieces"] =  move.purchase_line_id.di_nb_pieces - move.purchase_line_id.get_nb_pieces_enliv()
                                vals["di_nb_colis"] =  move.purchase_line_id.di_nb_colis - move.purchase_line_id.get_nb_colis_enliv()
                                vals["di_poin"] =  move.purchase_line_id.di_poin - move.purchase_line_id.get_poin_enliv()
                                vals["di_poib"] =  move.purchase_line_id.di_poib - move.purchase_line_id.get_poib_enliv()
                                vals["di_nb_palette"] =  move.purchase_line_id.di_nb_palette - move.purchase_line_id.get_nb_palette_enliv()
                                vals["di_qte_un_saisie"] =  move.purchase_line_id.di_qte_un_saisie - move.purchase_line_id.get_qte_un_saisie_enliv()
                                vals["di_tare"] =  move.purchase_line_id.di_tare
                                vals["di_tare_un"] =  move.purchase_line_id.di_tare_un 
                                if move.product_id.tracking != 'none':
                                    if move.purchase_line_id.order_id.id != False:
                                        lotexist = self.env['stock.production.lot'].search(['&', ('name', '=', move.purchase_line_id.order_id.name), ('product_id', '=', move.product_id.id)])
                                        if not lotexist:
                                            data = {
                                            'name': move.purchase_line_id.order_id.name,
                                            'product_id' : move.product_id.id                                      
                                            }            
                                            
                                            lot = self.env['stock.production.lot'].create(data)  # création du lot
                                            # self.env.cr.commit()# SC 23/08/2018 : Pas nécessaire de faire le commit pour que l'enreg soit utilisé       
                                                                   
                                            vals['lot_id'] = lot.id 
                                            vals['lot_name'] = lot.name
                                        else:
                                            vals['lot_id'] = lotexist.id 
                                            vals['lot_name'] = lotexist.name
                            
                        if not vals.get('lot_id') and  move.product_id.tracking != 'none':            
                            picking = self.env['stock.picking'].browse(vals['picking_id'])
                            lotexist = self.env['stock.production.lot'].search(['&', ('name', '=', picking.name), ('product_id', '=', move.product_id.id)])
                            if not lotexist:
                                data = {
                                'name': picking.name,
                                'product_id' : move.product_id.id                                        
                                } 
                                lot = self.env['stock.production.lot'].create(data)
                                # self.env.cr.commit()# SC 23/08/2018 : Pas nécessaire de faire le commit pour que l'enreg soit utilisé
                                vals['lot_id'] = lot.id
                                vals['lot_name'] = lot.name
                            else:
                                vals['lot_id'] = lotexist.id
                                vals['lot_name'] = lotexist.name
        
        ml = super(StockMoveLine, self).create(vals)
        if ml.di_poib - (ml.di_poin + ml.di_tare) < -0.001 or  ml.di_poib - (ml.di_poin + ml.di_tare) > 0.001:
            if not ml.di_poin:
                tare = ml.di_poib
            else:
                if not ml.di_poib:
                    tare = 0 - ml.di_poin
                else:
                    tare = ml.di_poib - ml.di_poin
            if not tare:
                tare = 0.0
            ml.di_tare = tare    
#         ml.update({'di_tare':tare})
            
        if ml.location_dest_id.usage=='customer':
            articles = ml.mapped('product_id')
            articles.update({
                    'di_flg_avec_ventes': True,
                })
        return ml
    
    def write(self, vals):
        ml = super(StockMoveLine, self).write(vals)
        for sml in self:
            if sml.di_poib - (sml.di_poin + sml.di_tare) < -0.001 or  sml.di_poib - (sml.di_poin + sml.di_tare) > 0.001:
                if not sml.di_poin:
                    tare = sml.di_poib
                else:
                    if not sml.di_poib:
                        tare = 0 - sml.di_poin
                    else:
                        tare = sml.di_poib - sml.di_poin
                if not tare:
                    tare = 0.0
                sml.di_tare = tare    
       
        return ml 
    
    def di_qte_spe_en_stock(self, product_id, date, lot,usage='internal'):            
        nbcol = 0.0
        nbpal = 0.0
        nbpiece = 0.0
        poids = 0.0
        qte_std = 0.0    
        poib = 0.0
        
#         time.strftime('%Y-%m-%d')
        if date:                
            di_date_to = date.strftime('%Y-%m-%d') + ' 23:59:59'   
            
            
        if lot:
            if date :   
                sqlstr = """
                    select
                        SUM ( Case when sml.di_usage_loc_dest = 'internal' then sml.di_nb_colis else -1*sml.di_nb_colis end) AS di_col_stock,
                        SUM ( Case when sml.di_usage_loc_dest = 'internal' then sml.qty_done else -1*sml.qty_done end) AS di_qte_stock,
                        SUM ( Case when sml.di_usage_loc_dest = 'internal' then sml.di_poib else -1*sml.di_poib end) AS di_poib_stock,
                        SUM ( Case when sml.di_usage_loc_dest = 'internal' then sml.di_poin else -1*sml.di_poin end) AS di_poin_stock,
                        SUM ( Case when sml.di_usage_loc_dest = 'internal' then sml.di_nb_pieces else -1*sml.di_nb_pieces end) AS di_piece_stock,
                        SUM ( Case when sml.di_usage_loc_dest = 'internal' then sml.di_nb_palette else -1*sml.di_nb_palette end) AS di_pal_stock                                                                                                                        
                    from stock_move_line sml                                    
                    LEFT JOIN (select di_cout.di_cmp,di_cout.id,di_cout.di_product_id from di_cout ) cmp on cmp.id = 
                    (select id from di_cout where di_product_id = sml.product_id order by di_date desc limit 1)
                    LEFT JOIN (select sm.sale_line_id, sm.id  from stock_move sm) sm on sm.id = sml.move_id
                    LEFT JOIN (select sol.price_unit, sol.id from sale_order_line sol) sol on sol.id = sm.sale_line_id   
                    LEFT JOIN stock_production_lot lot on lot.id = sml.lot_id                     
                    where sml.product_id = %s and sml.state ='done'  and sml.date <=%s and sml.lot_id = %s and lot.di_fini is false
                    """
                    
                self.env.cr.execute(sqlstr, (product_id.id, di_date_to,lot.id))
            else:
                sqlstr = """
                    select
                        SUM ( Case when sml.di_usage_loc_dest = 'internal' then sml.di_nb_colis else -1*sml.di_nb_colis end) AS di_col_stock,
                        SUM ( Case when sml.di_usage_loc_dest = 'internal' then sml.qty_done else -1*sml.qty_done end) AS di_qte_stock,
                        SUM ( Case when sml.di_usage_loc_dest = 'internal' then sml.di_poib else -1*sml.di_poib end) AS di_poib_stock,
                        SUM ( Case when sml.di_usage_loc_dest = 'internal' then sml.di_poin else -1*sml.di_poin end) AS di_poin_stock,
                        SUM ( Case when sml.di_usage_loc_dest = 'internal' then sml.di_nb_pieces else -1*sml.di_nb_pieces end) AS di_piece_stock,
                        SUM ( Case when sml.di_usage_loc_dest = 'internal' then sml.di_nb_palette else -1*sml.di_nb_palette end) AS di_pal_stock                                                                                                                        
                    from stock_move_line sml                                    
                    LEFT JOIN (select di_cout.di_cmp,di_cout.id,di_cout.di_product_id from di_cout ) cmp on cmp.id = 
                    (select id from di_cout where di_product_id = sml.product_id order by di_date desc limit 1)
                    LEFT JOIN (select sm.sale_line_id, sm.id  from stock_move sm) sm on sm.id = sml.move_id
                    LEFT JOIN (select sol.price_unit, sol.id from sale_order_line sol) sol on sol.id = sm.sale_line_id 
                    LEFT JOIN stock_production_lot lot on lot.id = sml.lot_id                       
                    where sml.product_id = %s and sml.state ='done'  and sml.lot_id = %s and lot.di_fini is false
                    """
                    
                self.env.cr.execute(sqlstr, (product_id.id, lot.id))
        else:
            if date :   
                sqlstr = """
                    select
                        SUM ( Case when sml.di_usage_loc_dest = 'internal' then sml.di_nb_colis else -1*sml.di_nb_colis end) AS di_col_stock,
                        SUM ( Case when sml.di_usage_loc_dest = 'internal' then sml.qty_done else -1*sml.qty_done end) AS di_qte_stock,
                        SUM ( Case when sml.di_usage_loc_dest = 'internal' then sml.di_poib else -1*sml.di_poib end) AS di_poib_stock,
                        SUM ( Case when sml.di_usage_loc_dest = 'internal' then sml.di_poin else -1*sml.di_poin end) AS di_poin_stock,
                        SUM ( Case when sml.di_usage_loc_dest = 'internal' then sml.di_nb_pieces else -1*sml.di_nb_pieces end) AS di_piece_stock,
                        SUM ( Case when sml.di_usage_loc_dest = 'internal' then sml.di_nb_palette else -1*sml.di_nb_palette end) AS di_pal_stock                                                                                                                        
                    from stock_move_line sml                                    
                    LEFT JOIN (select di_cout.di_cmp,di_cout.id,di_cout.di_product_id from di_cout ) cmp on cmp.id = 
                    (select id from di_cout where di_product_id = sml.product_id order by di_date desc limit 1)
                    LEFT JOIN (select sm.sale_line_id, sm.id  from stock_move sm) sm on sm.id = sml.move_id
                    LEFT JOIN (select sol.price_unit, sol.id from sale_order_line sol) sol on sol.id = sm.sale_line_id   
                    LEFT JOIN stock_production_lot lot on lot.id = sml.lot_id                     
                    where sml.product_id = %s and sml.state ='done'  and sml.date <=%s  and lot.di_fini is false
                    """
                    
                self.env.cr.execute(sqlstr, (product_id.id, di_date_to))
            else:
                sqlstr = """
                    select
                        SUM ( Case when sml.di_usage_loc_dest = 'internal' then sml.di_nb_colis else -1*sml.di_nb_colis end) AS di_col_stock,
                        SUM ( Case when sml.di_usage_loc_dest = 'internal' then sml.qty_done else -1*sml.qty_done end) AS di_qte_stock,
                        SUM ( Case when sml.di_usage_loc_dest = 'internal' then sml.di_poib else -1*sml.di_poib end) AS di_poib_stock,
                        SUM ( Case when sml.di_usage_loc_dest = 'internal' then sml.di_poin else -1*sml.di_poin end) AS di_poin_stock,
                        SUM ( Case when sml.di_usage_loc_dest = 'internal' then sml.di_nb_pieces else -1*sml.di_nb_pieces end) AS di_piece_stock,
                        SUM ( Case when sml.di_usage_loc_dest = 'internal' then sml.di_nb_palette else -1*sml.di_nb_palette end) AS di_pal_stock                                                                                                                        
                    from stock_move_line sml                                    
                    LEFT JOIN (select di_cout.di_cmp,di_cout.id,di_cout.di_product_id from di_cout ) cmp on cmp.id = 
                    (select id from di_cout where di_product_id = sml.product_id order by di_date desc limit 1)
                    LEFT JOIN (select sm.sale_line_id, sm.id  from stock_move sm) sm on sm.id = sml.move_id
                    LEFT JOIN (select sol.price_unit, sol.id from sale_order_line sol) sol on sol.id = sm.sale_line_id     
                    LEFT JOIN stock_production_lot lot on lot.id = sml.lot_id                   
                    where sml.product_id = %s and sml.state ='done' and lot.di_fini is false
                    """
                    
                self.env.cr.execute(sqlstr, (product_id.id,))                                        
        
        result = self.env.cr.fetchall()[0]
        nbcol = result[0] and result[0] or 0.0
        qte_std = result[1] and result[1] or 0.0
        poib = result[2] and result[2] or 0.0
        poids = result[3] and result[3] or 0.0
        nbpiece = result[4] and result[4] or 0.0
        nbpal = result[5] and result[5] or 0.0

        
        
#         if lot:               
#             if date:
#     #             mouvs=self.env['stock.move'].search(['&',('product_id','=',product_id),('state','=','done'),('picking_id','=',False),('inventory_id.date','=',date),('product_uom_qty','!=',0.0)])
#                 mouvs = self.env['stock.move.line'].search(['&', ('product_id', '=', product_id.id), ('lot_id', '=', lot.id), ('move_id.state', '=', 'done')]).filtered(lambda mv: mv.move_id.date.date() <= date)
#             else:
#                 mouvs = self.env['stock.move.line'].search([('product_id', '=', product_id.id), ('lot_id', '=', lot.id), ('move_id.state', '=', 'done')])
#         else:
#             if date:
#     #             mouvs=self.env['stock.move'].search(['&',('product_id','=',product_id),('state','=','done'),('picking_id','=',False),('inventory_id.date','=',date),('product_uom_qty','!=',0.0)])
#                 mouvs = self.env['stock.move.line'].search(['&', ('product_id', '=', product_id.id), ('move_id.state', '=', 'done')]).filtered(lambda mv: mv.move_id.date.date() <= date)
#             else:
#                 mouvs = self.env['stock.move.line'].search([('product_id', '=', product_id.id), ('move_id.state', '=', 'done')])
#              
#         for mouv in mouvs:
# #             if mouv.move_id.remaining_qty:
#             if mouv.location_dest_id.usage == usage:                
#                 nbcol = nbcol + mouv.di_nb_colis
#                 nbpal = nbpal + mouv.di_nb_palette
#                 nbpiece = nbpiece + mouv.di_nb_pieces
#                 poids = poids + mouv.di_poin
#                 poib = poib + mouv.di_poib
#                 qte_std = qte_std + mouv.qty_done                    
#             else:                
#                 nbcol = nbcol - mouv.di_nb_colis
#                 nbpal = nbpal - mouv.di_nb_palette
#                 nbpiece = nbpiece - mouv.di_nb_pieces
#                 poids = poids - mouv.di_poin
#                 poib = poib - mouv.di_poib
#                 qte_std = qte_std - mouv.qty_done                                       
                
        return (nbcol, nbpal, nbpiece, poids, qte_std,poib)
    
    
class StockPicking(models.Model):
    _inherit = 'stock.picking'
       
    
    di_nbpal = fields.Float(compute='_compute_di_nbpal_nbcol', digits=dp.get_precision('Product Unit of Measure'))
    di_nbcol = fields.Float(compute='_compute_di_nbpal_nbcol', digits=(8,1))
    di_poin = fields.Float(compute='_compute_di_nbpal_nbcol', digits=dp.get_precision('Product Unit of Measure'))
    di_poib = fields.Float(compute='_compute_di_nbpal_nbcol', digits=dp.get_precision('Product Unit of Measure'))
    di_tournee = fields.Char(string="Tournée", compute='_compute_tournee', store=True)
    di_rangtournee = fields.Char(string="Rang dans la tournée", compute='_compute_tournee', store=True)
    di_nbex = fields.Integer("Nombre exemplaires", help="""Nombre d'exemplaires d'une impression.""", default=0)
    
    @api.one
    @api.depends('move_lines')
    def _compute_di_nbpal_nbcol(self):        
        wnbpal = sum([move.di_nb_palette for move in self.move_lines if move.state != 'cancel'])
        wnbcol = sum([move.di_nb_colis for move in self.move_lines if move.state != 'cancel'])
        wpoin = sum([move.di_poin for move in self.move_lines if move.state != 'cancel'])
        wpoib = sum([move.di_poib for move in self.move_lines if move.state != 'cancel'])
        self.di_nbpal = wnbpal
        self.di_nbcol = wnbcol
        self.di_poin = wpoin
        self.di_poib = wpoib
            
    @api.model
    def create(self, vals):        
        res = super(StockPicking, self).create(vals)        
        for sp in res:   
            if sp.di_nbex == 0: 
                if sp.partner_id:                
                    sp.write({'di_nbex': sp.partner_id.di_nbex_bl})                
        return res
        
    @api.multi
    @api.onchange("partner_id")
    def di_onchange_partner(self):
        for bl in self:
            if bl.partner_id:
                bl.di_nbex = bl.partner_id.di_nbex_bl
    
   
        
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
    _order = "product_id"
    
    di_cmp = fields.Float(string="Coût moyen", related="product_id.standard_price", group_operator='avg', store=True)
    di_valstock = fields.Float(string='Valeur Stock', compute='_compute_valstock', group_operator='sum', store=True)
#     di_nb_pieces = fields.Integer(string='Nb pièces' , compute="_compute_qte_spe", group_operator='sum', store=True)
#     di_nb_palettes = fields.Integer(string='Nb palettes' , compute="_compute_qte_spe", group_operator='sum', store=True)

#     di_poin = fields.Float(string='Poids net', compute="_compute_qte_spe", group_operator='sum', store=True)
#     di_poib = fields.Float(string='Poids brut', compute="_compute_qte_spe", group_operator='sum', store=True)
#     di_tare = fields.Float(string='Tare', compute="_compute_qte_spe", group_operator='sum', store=True)
    di_nb_pieces = fields.Integer(string='Nb pièces' , compute="_compute_qte_spe", group_operator='sum', store=False)
    di_nb_palettes = fields.Integer(string='Nb palettes' , compute="_compute_qte_spe", group_operator='sum', store=False)
    di_nb_colis = fields.Float(string='Nb colis', compute="_compute_qte_spe", group_operator='sum', store=False, digits=(8,1))
    di_poin = fields.Float(string='Poids net', compute="_compute_qte_spe", group_operator='sum', store=False)
    di_poib = fields.Float(string='Poids brut', compute="_compute_qte_spe", group_operator='sum', store=False)
    di_tare = fields.Float(string='Tare', compute="_compute_qte_spe", group_operator='sum', store=False)
    
    currency_id = fields.Many2one("res.currency", related='company_id.currency_id', string="Currency")  # pour avoir le widget euro
    
    @api.multi
    @api.depends('di_cmp', 'quantity')
    def _compute_valstock(self):
        for quant in self:
            quant.di_valstock = quant.quantity * quant.di_cmp
            
            
    @api.multi    
    def _compute_qte_spe(self):
        for quant in self:     
            if quant.location_id.usage=='internal':
               (nbcol,nbpal,nbpiece,poin,qte,poib)= self.env['stock.move.line'].di_qte_spe_en_stock(quant.product_id,False,quant.lot_id,quant.location_id.usage)
               quant.di_nb_colis  = nbcol
               quant.di_nb_pieces  = nbpiece
               quant.di_nb_palettes  = nbpal
               quant.di_poin  = poin
               quant.di_poib  = poib                
                
           
class StockReturnPicking(models.TransientModel):
    _inherit = "stock.return.picking"
    
    @api.model
    def default_get(self, fields):
        # copie standard
        if len(self.env.context.get('active_ids', list())) > 1:
            raise UserError(_("You may only return one picking at a time."))
        res = super(StockReturnPicking, self).default_get(fields)

        move_dest_exists = False
        product_return_moves = []
        picking = self.env['stock.picking'].browse(self.env.context.get('active_id'))
        if picking:
            res.update({'picking_id': picking.id})
            if picking.state != 'done':
                raise UserError(_("You may only return Done pickings."))
            for move in picking.move_lines:
                if move.scrapped:
                    continue
                if move.move_dest_ids:
                    move_dest_exists = True
                plusieurs_lots = False    
                dernier_lot = False
                if move.move_line_ids:
                    for move_line in move.move_line_ids:
                        if move_line.lot_id and move_line.lot_id != dernier_lot and dernier_lot != False:
                            plusieurs_lots=True
                        dernier_lot = move_line.lot_id
                        
                        
                    if not plusieurs_lots:
                        di_lot = dernier_lot.id 
                    else:
                        di_lot = 0
                else:
                    di_lot=0      
                #surcharge
                di_qte_un_saisie = move.di_qte_un_saisie - sum(move.move_dest_ids.filtered(lambda m: m.state in ['partially_available', 'assigned', 'done']).\
                                                  mapped('move_line_ids').mapped('di_qte_un_saisie'))
                di_nb_pieces = move.di_nb_pieces - sum(move.move_dest_ids.filtered(lambda m: m.state in ['partially_available', 'assigned', 'done']).\
                                                  mapped('move_line_ids').mapped('di_nb_pieces'))
                di_nb_colis = move.di_nb_colis - sum(move.move_dest_ids.filtered(lambda m: m.state in ['partially_available', 'assigned', 'done']).\
                                                  mapped('move_line_ids').mapped('di_nb_colis'))
                di_nb_palette = move.di_nb_palette - sum(move.move_dest_ids.filtered(lambda m: m.state in ['partially_available', 'assigned', 'done']).\
                                                  mapped('move_line_ids').mapped('di_nb_palette'))
                di_poin = move.di_poin - sum(move.move_dest_ids.filtered(lambda m: m.state in ['partially_available', 'assigned', 'done']).\
                                                  mapped('move_line_ids').mapped('di_poin'))
                di_poib = move.di_poib - sum(move.move_dest_ids.filtered(lambda m: m.state in ['partially_available', 'assigned', 'done']).\
                                                  mapped('move_line_ids').mapped('di_poib'))
                di_tare = di_poib - di_poin     
                
                if di_nb_colis!= 0.0:
                    di_tare_un = di_tare / ceil(di_nb_colis)
                else: 
                    di_tare_un = di_tare 
    
                quantity = move.product_qty - sum(move.move_dest_ids.filtered(lambda m: m.state in ['partially_available', 'assigned', 'done']).\
                                                  mapped('move_line_ids').mapped('product_qty'))
                quantity = float_round(quantity, precision_rounding=move.product_uom.rounding)
                product_return_moves.append((0, 0, {'product_id': move.product_id.id,'di_lot_id':di_lot, 'quantity': quantity, 'di_qte_un_saisie': di_qte_un_saisie, 'di_nb_pieces': di_nb_pieces, 'di_nb_colis': di_nb_colis, 'di_nb_palette': di_nb_palette, 'di_poin': di_poin, 'di_poib': di_poib, 'di_tare': di_tare, 'di_tare_un': di_tare_un, 'move_id': move.id, 'uom_id': move.product_id.uom_id.id}))
                #fin surcharge
            if not product_return_moves:
                raise UserError(_("No products to return (only lines in Done state and not fully returned yet can be returned)."))
            if 'product_return_moves' in fields:
                res.update({'product_return_moves': product_return_moves})
            if 'move_dest_exists' in fields:
                res.update({'move_dest_exists': move_dest_exists})
            if 'parent_location_id' in fields and picking.location_id.usage == 'internal':
                res.update({'parent_location_id': picking.picking_type_id.warehouse_id and picking.picking_type_id.warehouse_id.view_location_id.id or picking.location_id.location_id.id})
            if 'original_location_id' in fields:
                res.update({'original_location_id': picking.location_id.id})
            if 'location_id' in fields:
                location_id = picking.location_id.id
                if picking.picking_type_id.return_picking_type_id.default_location_dest_id.return_location:
                    location_id = picking.picking_type_id.return_picking_type_id.default_location_dest_id.id
                res['location_id'] = location_id
        return res

    def _create_returns(self):
        #copie standard
        # TODO sle: the unreserve of the next moves could be less brutal
        for return_move in self.product_return_moves.mapped('move_id'):
            return_move.move_dest_ids.filtered(lambda m: m.state not in ('done', 'cancel'))._do_unreserve()

        # create new picking for returned products
        picking_type_id = self.picking_id.picking_type_id.return_picking_type_id.id or self.picking_id.picking_type_id.id
        new_picking = self.picking_id.copy({
            'move_lines': [],
            'picking_type_id': picking_type_id,
            'state': 'draft',
            'origin': _("Return of %s") % self.picking_id.name,
            'location_id': self.picking_id.location_dest_id.id,
            'location_dest_id': self.location_id.id})
        new_picking.message_post_with_view('mail.message_origin_link',
            values={'self': new_picking, 'origin': self.picking_id},
            subtype_id=self.env.ref('mail.mt_note').id)
        returned_lines = 0
        for return_line in self.product_return_moves:
            if not return_line.move_id:
                raise UserError(_("You have manually created product lines, please delete them to proceed."))
            # TODO sle: float_is_zero?
            if return_line.quantity:
                returned_lines += 1
                vals = self._prepare_move_default_values(return_line, new_picking)
                r = return_line.move_id.copy(vals)
                vals = {}

                # +--------------------------------------------------------------------------------------------------------+
                # |       picking_pick     <--Move Orig--    picking_pack     --Move Dest-->   picking_ship
                # |              | returned_move_ids              ↑                                  | returned_move_ids
                # |              ↓                                | return_line.move_id              ↓
                # |       return pick(Add as dest)          return toLink                    return ship(Add as orig)
                # +--------------------------------------------------------------------------------------------------------+
                move_orig_to_link = return_line.move_id.move_dest_ids.mapped('returned_move_ids')
                move_dest_to_link = return_line.move_id.move_orig_ids.mapped('returned_move_ids')
                vals['move_orig_ids'] = [(4, m.id) for m in move_orig_to_link | return_line.move_id]
                vals['move_dest_ids'] = [(4, m.id) for m in move_dest_to_link]
                r.write(vals)
                for sml in r.move_line_ids:
#                     sml.di_qte_un_saisie = return_line.di_qte_un_saisie
#                     sml.di_nb_pieces = return_line.di_nb_pieces
#                     sml.di_nb_colis = return_line.di_nb_colis
#                     sml.di_nb_palette = return_line.di_nb_palette
#                     sml.di_poin = return_line.di_poin
#                     sml.di_poib = return_line.di_poib
#                     sml.di_tare = return_line.di_tare
#                     sml.di_tare_un = return_line.di_tare_un
                    sml.update({'di_qte_un_saisie':return_line.di_qte_un_saisie,
                                'di_nb_pieces':return_line.di_nb_pieces,
                                'di_nb_colis':return_line.di_nb_colis,
                                'di_nb_palette':return_line.di_nb_palette,
                                'di_poin':return_line.di_poin,
                                'di_poib':return_line.di_poib,
                                'di_tare':return_line.di_tare,
                                'di_tare_un':return_line.di_tare_un,
                                'lot_id':return_line.di_lot_id.id
                                })
                                
        if not returned_lines:
            raise UserError(_("Please specify at least one non-zero quantity."))

        new_picking.action_confirm()
        new_picking.action_assign()
        
        for move in new_picking.move_lines:
            return_picking_line = self.product_return_moves.filtered(lambda r: r.move_id == move.origin_returned_move_id)
            if return_picking_line and return_picking_line.to_refund:
                move.to_refund = True
        return new_picking.id, picking_type_id

   

class StockReturnPickingLine(models.TransientModel):
    _inherit = "stock.return.picking.line"
    
    di_qte_un_saisie = fields.Float(string='Quantité en unité de saisie', store=True, compute="_compute_qte_un_saisie")
    di_nb_pieces = fields.Integer(string='Nb pièces')
    di_nb_colis = fields.Float(string='Nb colis' , digits=(8,1))
    di_nb_palette = fields.Float(string='Nb palettes', digits=dp.get_precision('Product Unit of Measure'))
    di_poin = fields.Float(string='Poids net' )
    di_poib = fields.Float(string='Poids brut')
    di_tare = fields.Float(string='Tare' )    
    di_tare_un = fields.Float(string='Tare unitaire')
    di_flg_modif_uom = fields.Boolean(default=False)
    di_flg_modif_qty_spe = fields.Boolean(default=False)
    di_lot_id = fields.Many2one('stock.production.lot', 'Lot')
    
    
    @api.multi    
    @api.depends('di_poin', 'di_tare', 'di_nb_colis', 'di_nb_pieces', 'di_nb_palette')
    def _compute_qte_un_saisie(self):
        # recalcule la quantité en unité de saisie
        for srpl in self:
            
            move = srpl.move_id
             
            if move.di_un_saisie == "PIECE":
                srpl.di_qte_un_saisie = srpl.di_nb_pieces
            elif move.di_un_saisie == "COLIS":
                srpl.di_qte_un_saisie = srpl.di_nb_colis
            elif move.di_un_saisie == "PALETTE":
                srpl.di_qte_un_saisie = srpl.di_nb_palette
            elif move.di_un_saisie == "KG":
                srpl.di_qte_un_saisie = srpl.di_poib
            else:
                srpl.di_qte_un_saisie = srpl.quantity   
    
    @api.multi                     
    @api.onchange('di_nb_palette')
    def _di_change_nb_palette(self):
        if self.ensure_one():
            if self.di_flg_modif_uom == False:
                self.di_flg_modif_qty_spe = True   
                move = self.move_id                                      
                if move.di_type_palette_id:
                    self.di_nb_colis = round(self.di_nb_palette * move.di_type_palette_id.di_qte_cond_inf,1)  
                    nbcol = round(self.di_nb_colis,1)                  
                    if move.product_uom.name.lower() == 'kg':       
#                         self.quantity = move.di_product_packaging_id.qty * self.di_nb_colis * self.product_id.weight
                        self.quantity = move.di_product_packaging_id.qty * nbcol * self.product_id.weight
                        self.di_poin = self.quantity 
                    else:                                  
#                         self.quantity = move.di_product_packaging_id.qty * self.di_nb_colis
                        self.quantity = move.di_product_packaging_id.qty * nbcol
                        self.di_poin = self.quantity  * self.product_id.weight
#                     self.di_nb_pieces = ceil(move.di_product_packaging_id.di_qte_cond_inf * self.di_nb_colis)            
                    self.di_nb_pieces = ceil(move.di_product_packaging_id.di_qte_cond_inf * nbcol)
                     
                    self.di_poib = self.di_poin + self.di_tare
      
    @api.multi                     
    @api.onchange('di_nb_colis')
    def _di_change_nb_colis(self):
        if self.ensure_one():
            if self.di_flg_modif_uom == False:
                self.di_flg_modif_qty_spe = True      
                self.di_tare_un = 0.0
                self.di_tare = 0.0
                move = self.move_id    
                if move.di_product_packaging_id: 
                    nbcol = round(self.di_nb_colis,1)
                    if move.product_uom.name.lower() == 'kg':       
#                         self.quantity = move.di_product_packaging_id.qty * self.di_nb_colis * self.product_id.weight
                        self.quantity = move.di_product_packaging_id.qty * nbcol * self.product_id.weight
                        self.di_poin = self.quantity  
                    else:                                  
#                         self.quantity = move.di_product_packaging_id.qty * self.di_nb_colis
                        self.quantity = move.di_product_packaging_id.qty * nbcol
                        self.di_poin = self.quantity  * self.product_id.weight
                          
#                     self.di_nb_pieces = ceil(move.di_product_packaging_id.di_qte_cond_inf * self.di_nb_colis)
                    self.di_nb_pieces = ceil(move.di_product_packaging_id.di_qte_cond_inf * nbcol)
                    if move.di_type_palette_id.di_qte_cond_inf != 0.0:                
#                         self.di_nb_palette = self.di_nb_colis / move.di_type_palette_id.di_qte_cond_inf
                        self.di_nb_palette = nbcol / move.di_type_palette_id.di_qte_cond_inf
                    else:
#                         self.di_nb_palette = self.di_nb_colis
                        self.di_nb_palette = nbcol
                    
                    self.di_poib = self.di_poin + self.di_tare
                
    @api.multi    
    @api.onchange('di_nb_colis', 'di_tare_un')
    def _di_recalcule_tare(self):
        if self.ensure_one():
            nbcol = round(self.di_nb_colis,1)
#             self.di_tare = self.di_tare_un * ceil(self.di_nb_colis)
            self.di_tare = self.di_tare_un * ceil(nbcol)
                
    @api.multi                     
    @api.onchange('di_nb_pieces')
    def _di_change_nb_pieces(self):
        if self.ensure_one():
            if self.di_flg_modif_uom == False:
                self.di_flg_modif_qty_spe = True      
                move = self.move_id
                if move.product_uom.name.lower() == 'kg':       
                    self.quantity = self.di_nb_pieces * self.product_id.weight 
                    self.di_poin = self.quantity  
                else:                                             
                    self.quantity =self.di_nb_pieces
                    self.di_poin = self.quantity  * self.product_id.weight
                self.di_poib = self.di_poin + self.di_tare

    @api.multi 
    @api.onchange('di_poib')
    def _di_onchange_poib(self):
        if self.ensure_one():
            if self.di_flg_modif_uom == False:
                self.di_flg_modif_qty_spe = True
                self.di_poin = self.di_poib - self.di_tare
                move = self.move_id                
                if move.product_uom.name.lower() == 'kg':
                    self.quantity = self.di_poin
   
    @api.multi 
    @api.onchange('di_tare')
    def _di_onchange_tare(self):
        if self.ensure_one():
            if self.di_flg_modif_uom == False:
                self.di_flg_modif_qty_spe = True    
                self.di_poin = self.di_poib - self.di_tare  
                move = self.move_id        
                if move.product_uom.name.lower() == 'kg':
                    self.quantity = self.di_poin
                    
    @api.multi 
    @api.onchange('di_poin')
    def _di_onchange_poin(self):
        if self.ensure_one(): 
            if self.di_flg_modif_uom == False:
                self.di_flg_modif_qty_spe = True     
                move = self.move_id                        
                if move.product_uom.name.lower() == 'kg':
                    self.quantity = self.di_poin               
                self.di_poib = self.di_poin + self.di_tare
    
    @api.multi                     
    @api.onchange('quantity')
    def _di_change_quantity(self):
        if self.ensure_one() :
            move = self.move_id              
            if self.di_flg_modif_qty_spe == False:
                if move.product_uom:
                    if move.product_uom.name.lower() == 'kg':
                        # si géré au kg, on ne modife que les champs poids
                        self.di_poin = self.quantity
                        self.di_poib = self.di_poin + self.di_tare
                    if move.product_uom.name == 'Unit(s)' or move.product_uom.name == 'Pièce' :
                        self.di_nb_pieces = ceil(self.qty_done)
                    if move.product_uom.name.lower() ==  'colis' :
                        self.di_nb_colis = round(self.qty_done,1)
                    if move.product_uom.name.lower() ==  'palette' :
                        self.di_nb_palette = ceil(self.qty_done) 
                                 
                    self.di_flg_modif_uom = True
            self.di_flg_modif_qty_spe=False

class StockProductionLot(models.Model):    
    _inherit = "stock.production.lot"
    _order= "create_date desc, name desc"
    
    di_fini = fields.Boolean("Lot clôturé", default=False, store=True, compute="_compute_cloture")
    
    @api.depends('quant_ids.quantity')
    def _compute_cloture(self):
        for lot in self:
            product_qty = 0.0
            quants = lot.quant_ids.filtered(lambda q: q.location_id.usage in ['internal', 'transit'])
            product_qty = sum(quants.mapped('quantity'))
            if product_qty != 0.0:
                lot.di_fini = False