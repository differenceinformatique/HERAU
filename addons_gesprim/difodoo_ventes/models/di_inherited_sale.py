
# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, float_compare
from datetime import datetime, timedelta
from odoo.exceptions import UserError, ValidationError, Warning
from ...difodoo_fichiers_base.controllers import di_ctrl_print
import ctypes
from math import ceil
from odoo.addons import decimal_precision as dp
from difodoo.addons_gesprim.difodoo_fichiers_base.models import di_param
from functools import partial
from odoo.tools.misc import formatLang


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"
    
    modifparprg = False
    
    di_qte_un_saisie= fields.Float(string='Quantité en unité de saisie',store=True)
    di_un_saisie    = fields.Selection([("PIECE", "Pièce"), ("COLIS", "Colis"),("PALETTE", "Palette"),("KG","Kg")], string="Unité de saisie",store=True)
    di_type_palette_id  = fields.Many2one('product.packaging', string='Palette') 
    di_nb_pieces    = fields.Integer(string='Nb pièces' ,compute="_compute_qte_aff",store=True)
    di_nb_colis     = fields.Integer(string='Nb colis',compute="_compute_qte_aff",store=True)
    di_nb_palette   = fields.Float(string='Nb palettes',compute="_compute_qte_aff",store=True)
    di_poin         = fields.Float(string='Poids net',compute="_compute_qte_aff",store=True)
    di_poib         = fields.Float(string='Poids brut',store=True)
    di_tare         = fields.Float(string='Tare',store=True)#,compute="_compute_tare")
    di_un_prix      = fields.Selection([("PIECE", "Pièce"), ("COLIS", "Colis"),("PALETTE", "Palette"),("KG","Kg")], string="Unité de prix",store=True)

    di_flg_modif_uom = fields.Boolean(store=True)

    di_qte_un_saisie_liv = fields.Float(string='Quantité livrée en unité de saisie', compute='_compute_qty_delivered')
    di_un_saisie_liv     = fields.Selection([("PIECE", "Pièce"), ("COLIS", "Colis"),("PALETTE", "Palette"),("KG","Kg")], string="Unité de saisie livrée")
    di_type_palette_liv_id  = fields.Many2one('product.packaging', string='Palette livrée') 
    di_nb_pieces_liv     = fields.Integer(string='Nb pièces livrées', compute='_compute_qty_delivered')
    di_nb_colis_liv      = fields.Integer(string='Nb colis livrés', compute='_compute_qty_delivered')
    di_nb_palette_liv    = fields.Float(string='Nb palettes livrées', compute='_compute_qty_delivered')
    di_poin_liv          = fields.Float(string='Poids net livré', compute='_compute_qty_delivered')
    di_poib_liv          = fields.Float(string='Poids brut livré', compute='_compute_qty_delivered')
    di_tare_liv          = fields.Float(string='Tare livrée', compute='_compute_qty_delivered')
    di_product_packaging_liv_id=fields.Many2one('product.packaging', string='Colis livré')
    
    di_qte_un_saisie_fac = fields.Float(string='Quantité facturée en unité de saisie',compute='_get_invoice_qty')
    di_un_saisie_fac     = fields.Selection([("PIECE", "Pièce"), ("COLIS", "Colis"),("PALETTE", "Palette"),("KG","Kg")], string="Unité de saisie facturés")
    di_type_palette_fac_id  = fields.Many2one('product.packaging', string='Palette facturée') 
    di_nb_pieces_fac     = fields.Integer(string='Nb pièces facturées')
    di_nb_colis_fac      = fields.Integer(string='Nb colis facturés')
    di_nb_palette_fac    = fields.Float(string='Nb palettes facturées')
    di_poin_fac          = fields.Float(string='Poids net facturé')
    di_poib_fac          = fields.Float(string='Poids brut facturé')
    di_tare_fac          = fields.Float(string='Tare facturée')
    di_product_packaging_fac_id=fields.Many2one('product.packaging', string='Colis facturé')
    di_un_prix_fac      = fields.Selection([("PIECE", "Pièce"), ("COLIS", "Colis"),("PALETTE", "Palette"),("KG","Kg")], string="Unité de prix facturé",store=True)
    
    di_qte_a_facturer_un_saisie = fields.Float(string='Quantité à facturer en unité de saisie',compute='_get_to_invoice_qty')
    
    di_spe_saisissable = fields.Boolean(string='Champs spé saisissables',default=True,compute='_di_compute_spe_saisissable',store=True)
          
    di_dern_prix = fields.Float(string='Dernier prix', digits=dp.get_precision('Product Price'),compute='_di_compute_dernier_prix',store=True)
    
    di_marge_prc = fields.Float(string='% marge',compute='_di_calul_marge_prc',store=True)
    
    di_marge_inf_seuil = fields.Boolean(string='Marge inférieure au seuil',default = False, compute='_di_compute_marge_seuil',store=True)
    
    @api.multi
    @api.depends('move_ids.state', 'move_ids.scrapped', 'move_ids.product_uom_qty', 'move_ids.product_uom', 'move_ids.di_qte_un_saisie'
                 , 'move_ids.di_nb_pieces', 'move_ids.di_nb_colis', 'move_ids.di_nb_palette', 'move_ids.di_poin', 'move_ids.di_poib')
    def _compute_qty_delivered(self):
        super(SaleOrderLine, self)._compute_qty_delivered()

        for line in self:  # TODO: maybe one day, this should be done in SQL for performance sake
            if line.qty_delivered_method == 'stock_move':
                qte_un_saisie = 0.0
                pieces = 0.0
                colis = 0.0
                palettes = 0.0
                poib = 0.0
                poin = 0.0
                
                for move in line.move_ids.filtered(lambda r: r.state == 'done' and not r.scrapped and line.product_id == r.product_id):
                    if move.location_dest_id.usage == "customer":
                        if not move.origin_returned_move_id or (move.origin_returned_move_id and move.to_refund):
                            qte_un_saisie += move.di_qte_un_saisie
                            pieces += move.di_nb_pieces
                            colis += move.di_nb_colis
                            palettes += move.di_nb_palette
                            poib += move.di_poib
                            poin += move.di_poin
                   
                    elif move.location_dest_id.usage != "customer" and move.to_refund:
                        qte_un_saisie -= move.di_qte_un_saisie
                        pieces -= move.di_nb_pieces
                        colis -= move.di_nb_colis
                        palettes -= move.di_nb_palette
                        poib -= move.di_poib
                        poin -= move.di_poin
                        
                    line.di_type_palette_liv_id  = move.di_type_palette_id
                    line.di_un_saisie_liv     = move.di_un_saisie
                    line.di_product_packaging_liv_id = move.di_product_packaging_id
                    line.di_tare_liv          = move.di_tare 
               
                line.di_qte_un_saisie_liv = qte_un_saisie
                line.di_nb_pieces_liv = pieces
                line.di_nb_colis_liv = colis
                line.di_nb_palette_liv = palettes
                line.di_poib_liv = poib
                line.di_poin_liv = poin
                
    @api.multi
    @api.depends('di_marge_prc','company_id.di_param_id.di_seuil_marge_prc')#,'di_param_id.di_seuil_marge_prc')
    def _di_compute_marge_seuil(self):   
        for sol in self:
            if sol.di_marge_prc < sol.company_id.di_param_id.di_seuil_marge_prc:     
                sol.di_marge_inf_seuil = True
            else:
                sol.di_marge_inf_seuil = False
            
    
    @api.multi
    @api.depends('price_subtotal','product_uom_qty','purchase_price')
    def _di_calul_marge_prc(self):
        for sol in self:
            if sol.product_uom_qty and sol.product_uom_qty != 0.0:
                qte = sol.product_uom_qty
            else:
                qte = 1.0
            if sol.purchase_price and sol.purchase_price !=0.0:
                sol.di_marge_prc = (sol.price_subtotal/qte - sol.purchase_price )*100/sol.purchase_price            
            else:
                sol.di_marge_prc = sol.price_subtotal/qte*100
        
        
    def _get_dernier_prix(self):
        prix = 0.0
        l = self.search(['&', ('product_id', '=', self.product_id.id), ('order_partner_id', '=', self.order_partner_id.id),('order_id.date_order','<',self.order_id.date_order)], limit=1).sorted(key=lambda t: t.order_id.date_order,reverse=True)
        if l.price_unit:
            prix = l.price_unit            
        return prix
    
    @api.multi
    @api.onchange('di_type_palette_id','product_packaging','di_nb_colis','di_nb_palette')
    def _compute_tare(self):        
        self.di_tare = (self.di_type_palette_id.di_poids * self.di_nb_palette) + (self.product_packaging.di_poids * self.di_nb_colis)
    
    
    @api.multi
    @api.depends('product_id','order_partner_id','order_id.date_order')
    def _di_compute_dernier_prix(self):        
        for sol in self:
            sol.di_dern_prix =sol._get_dernier_prix()
            
#     @api.model
#     def create(self, vals):         
#         line = False              
#         if vals['product_uom_qty'] and vals['product_uom_qty']!=0.0:
#             line = super(SaleOrderLine, self).create(vals)                                
#         return line
    
              
    def di_recherche_prix_unitaire(self,prixOrig, tiers, article, di_un_prix , qte, date,typecol,typepal):    
        prixFinal = 0.0       
        prixFinal =self.env["di.tarifs"]._di_get_prix(tiers,article,di_un_prix,qte,date,typecol,typepal)
        if prixFinal == 0.0:
            prixFinal = prixOrig
#             if prixOrig == 0.0:
#                 raise ValidationError("Le prix unitaire de la ligne est à 0 !")
        return prixFinal  
                       
    @api.multi
    @api.depends('product_id.di_spe_saisissable','product_id','di_qte_un_saisie')
    def _di_compute_spe_saisissable(self):     
        for sol in self:   
            sol.di_spe_saisissable =sol.product_id.di_spe_saisissable
     

    @api.depends('product_uom_qty', 'discount', 'price_unit', 'tax_id','di_qte_un_saisie','di_nb_pieces','di_nb_colis','di_nb_palette','di_poin','di_poib','di_tare','di_un_prix')
    def _compute_amount(self):
        # copie standard
        """
        Compute the amounts of the SO line.
        """
        for line in self:
            price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
            # modif de la quantité à prendre en compte
            di_qte_prix = 0.0
            if line.di_un_prix == "PIECE":
                di_qte_prix = line.di_nb_pieces
            elif line.di_un_prix == "COLIS":
                di_qte_prix = line.di_nb_colis
            elif line.di_un_prix == "PALETTE":
                di_qte_prix = line.di_nb_palette
            elif line.di_un_prix == "KG":
                di_qte_prix = line.di_poin
            elif line.di_un_prix == False or line.di_un_prix == '':
                di_qte_prix = line.product_uom_qty
             
            taxes = line.tax_id.compute_all(price, line.order_id.currency_id, di_qte_prix, product=line.product_id, partner=line.order_id.partner_shipping_id)
            line.update({
                'price_tax': sum(t.get('amount', 0.0) for t in taxes.get('taxes', [])),
                'price_total': taxes['total_included'],
                'price_subtotal': taxes['total_excluded'],
            })
       
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
    
               
    @api.multi
    @api.onchange('product_id')
    def _di_charger_valeur_par_defaut(self):
        if self.ensure_one():
            if self.order_partner_id and self.product_id:
                ref = self.env['di.ref.art.tiers'].search([('di_partner_id','=',self.order_partner_id.id),('di_product_id','=',self.product_id.id)],limit=1)
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
                   
                
    @api.multi
    @api.onchange('product_id')
    def product_id_change(self):
        result=super(SaleOrderLine, self).product_id_change()
        #surcharge de la procédure pour recalculer le prix car elle est appelée après _di_changer_prix quand on modifie l'article
        vals = {}
        if self.product_id and self.di_un_prix:
#             if vals.get("price_unit"):
            # modif de la quantité à prendre en compte
            di_qte_prix = 0.0
            if self.di_un_prix == "PIECE":
                di_qte_prix = self.di_nb_pieces
            elif self.di_un_prix == "COLIS":
                di_qte_prix = self.di_nb_colis
            elif self.di_un_prix == "PALETTE":
                di_qte_prix = self.di_nb_palette
            elif self.di_un_prix == "KG":
                di_qte_prix = self.di_poin
            elif self.di_un_prix == False or self.di_un_prix == '':
                di_qte_prix = self.product_uom_qty
                
            vals['price_unit'] = self.di_recherche_prix_unitaire(self.price_unit,self.order_id.partner_id,self.product_id,self.di_un_prix,di_qte_prix,self.order_id.date_order,self.product_packaging,self.di_type_palette_id)
            self.update(vals)       
        return result
    
    @api.onchange('product_uom', 'product_uom_qty')
    def product_uom_change(self):
        super(SaleOrderLine, self).product_uom_change()
        #surcharge de la procédure pour recalculer le prix car elle est appelée après _di_changer_prix quand on modifie l'article
        if self.product_id and self.di_un_prix:            
            di_qte_prix = 0.0
            if self.di_un_prix == "PIECE":
                di_qte_prix = self.di_nb_pieces
            elif self.di_un_prix == "COLIS":
                di_qte_prix = self.di_nb_colis
            elif self.di_un_prix == "PALETTE":
                di_qte_prix = self.di_nb_palette
            elif self.di_un_prix == "KG":
                di_qte_prix = self.di_poin
            elif self.di_un_prix == False or self.di_un_prix == '':
                di_qte_prix = self.product_uom_qty
            self.price_unit = self.di_recherche_prix_unitaire(self.price_unit,self.order_id.partner_id,self.product_id,self.di_un_prix,di_qte_prix,self.order_id.date_order,self.product_packaging,self.di_type_palette_id)       
                
    @api.multi
    @api.onchange('product_id','order_id.partner_id','order_id.date_order','di_un_prix','di_qte_un_saisie','di_nb_pieces','di_nb_colis','di_nb_palette','di_poin','di_poib','di_tare','product_uom_qty')
    def _di_changer_prix(self):
        for line in self:
            di_qte_prix = 0.0
            if line.di_un_prix == "PIECE":
                di_qte_prix = line.di_nb_pieces
            elif line.di_un_prix == "COLIS":
                di_qte_prix = line.di_nb_colis
            elif line.di_un_prix == "PALETTE":
                di_qte_prix = line.di_nb_palette
            elif line.di_un_prix == "KG":
                di_qte_prix = line.di_poin
            elif line.di_un_prix == False or line.di_un_prix == '':
                di_qte_prix = line.product_uom_qty             
            if line.product_id.id != False and line.di_un_prix:       
                line.price_unit = self.di_recherche_prix_unitaire(line.price_unit,line.order_id.partner_id,line.product_id,line.di_un_prix,di_qte_prix,line.order_id.date_order,line.product_packaging,line.di_type_palette_id)
    @api.multi 
    @api.onchange('di_poib')
    def _di_recalcule_tare(self):
        if self.ensure_one():
            self.di_tare = self.di_poib - self.di_poin
            
    @api.multi    
    @api.onchange('product_uom_qty')
    def _di_modif_qte_un_mesure(self):
        if self.ensure_one():
            if SaleOrderLine.modifparprg == False:
                if self.product_uom:
                    if self.product_uom.name.lower() == 'kg':
                        self.di_poin=self.product_uom_qty * self.product_id.weight
                        self.di_poib = self.di_poin + self.di_tare
                    elif self.product_uom.name.lower() != 'kg':    
                        if self.product_id.di_get_type_piece().qty != 0.0:
                            self.di_nb_pieces = ceil(self.product_uom_qty/self.product_id.di_get_type_piece().qty)
                        else:
                            self.di_nb_pieces = ceil(self.product_uom_qty)                                
                        if self.product_packaging.qty != 0.0 :
                            self.di_nb_colis = ceil(self.product_uom_qty / self.product_packaging.qty)
                        else:      
                            self.di_nb_colis = ceil(self.product_uom_qty)             
                        if self.di_type_palette_id.di_qte_cond_inf != 0.0:
                            self.di_nb_palette = self.di_nb_colis / self.di_type_palette_id.di_qte_cond_inf
                        else:
                            self.di_nb_palette = self.di_nb_colis
                        self.di_poin = self.product_uom_qty * self.product_id.weight 
                        self.di_poib = self.di_poin + self.di_tare
                    self.di_flg_modif_uom = True
            SaleOrderLine.modifparprg=False
    
    @api.multi    
    @api.onchange('di_qte_un_saisie', 'di_un_saisie','di_type_palette_id','di_tare','product_packaging')
    def _di_recalcule_quantites(self):
        if self.ensure_one():            
            if self.di_flg_modif_uom == False:
                SaleOrderLine.modifparprg=True
                if self.di_un_saisie == "PIECE":
                    self.di_nb_pieces = ceil(self.di_qte_un_saisie)
                    self.product_uom_qty = self.product_id.di_get_type_piece().qty * self.di_nb_pieces
                    if self.product_packaging.qty != 0.0 :
                        self.di_nb_colis = ceil(self.product_uom_qty / self.product_packaging.qty)
                    else:      
                        self.di_nb_colis = ceil(self.product_uom_qty)             
                    if self.di_type_palette_id.di_qte_cond_inf != 0.0:
                        self.di_nb_palette = self.di_nb_colis / self.di_type_palette_id.di_qte_cond_inf
                    else:
                        self.di_nb_palette = self.di_nb_colis
                    self.di_poin = self.product_uom_qty * self.product_id.weight 
                    self.di_poib = self.di_poin + self.di_tare
                          
                elif self.di_un_saisie == "COLIS":
                    self.di_nb_colis = ceil(self.di_qte_un_saisie)
                    self.product_uom_qty = self.product_packaging.qty * self.di_nb_colis
                    self.di_nb_pieces = ceil(self.product_packaging.di_qte_cond_inf * self.di_nb_colis)
                    if self.di_type_palette_id.di_qte_cond_inf !=0.0:                
                        self.di_nb_palette = self.di_nb_colis / self.di_type_palette_id.di_qte_cond_inf
                    else:
                        self.di_nb_palette = self.di_nb_colis
                    self.di_poin = self.product_uom_qty * self.product_id.weight 
                    self.di_poib = self.di_poin + self.di_tare
                                         
                elif self.di_un_saisie == "PALETTE":            
                    self.di_nb_palette = self.di_qte_un_saisie
                    if self.di_type_palette_id.di_qte_cond_inf!=0.0:
                        self.di_nb_colis = ceil(self.di_nb_palette / self.di_type_palette_id.di_qte_cond_inf)
                    else:
                        self.di_nb_colis = ceil(self.di_nb_palette)
                    self.di_nb_pieces = ceil(self.product_packaging.di_qte_cond_inf * self.di_nb_colis)
                    self.product_uom_qty = self.product_packaging.qty * self.di_nb_colis
                    self.di_poin = self.product_uom_qty * self.product_id.weight 
                    self.di_poib = self.di_poin + self.di_tare
                    
                elif self.di_un_saisie == "KG":

                    self.di_poin = self.di_qte_un_saisie
                    self.di_poib = self.di_poin + self.di_tare
                    self.product_uom_qty = self.di_poin
                    if self.product_packaging.qty !=0.0:
                        self.di_nb_colis = ceil(self.product_uom_qty / self.product_packaging.qty)
                    else:
                        self.di_nb_colis = ceil(self.product_uom_qty)
                    if self.di_type_palette_id.di_qte_cond_inf !=0.0:    
                        self.di_nb_palette = self.di_nb_colis / self.di_type_palette_id.di_qte_cond_inf
                    else:  
                        self.di_nb_palette = self.di_nb_colis
                    self.di_nb_pieces = ceil(self.product_packaging.di_qte_cond_inf * self.di_nb_colis)
                    
                else:
                    self.di_poin = self.di_qte_un_saisie
                    self.di_poib = self.di_poin + self.di_tare
                    self.product_uom_qty = self.di_poin
                    if self.product_packaging.qty !=0.0:
                        self.di_nb_colis = ceil(self.product_uom_qty / self.product_packaging.qty)
                    else:
                        self.di_nb_colis = ceil(self.product_uom_qty)
                    if self.di_type_palette_id.di_qte_cond_inf !=0.0:    
                        self.di_nb_palette = self.di_nb_colis / self.di_type_palette_id.di_qte_cond_inf
                    else:  
                        self.di_nb_palette = self.di_nb_colis
                    self.di_nb_pieces = ceil(self.product_packaging.di_qte_cond_inf * self.di_nb_colis)
                
    @api.multi
    @api.depends('di_qte_un_saisie', 'di_un_saisie','di_type_palette_id','product_packaging')
    def _compute_qte_aff(self):
        #if self.ensure_one():
        for sol in self:
            if sol.di_flg_modif_uom == False:
                if sol.di_un_saisie == "PIECE":
                    sol.di_nb_pieces = ceil(sol.di_qte_un_saisie)            
                    if sol.product_packaging.qty != 0.0 :
                        sol.di_nb_colis = ceil(sol.product_uom_qty / sol.product_packaging.qty)
                    else:      
                        sol.di_nb_colis = ceil(sol.product_uom_qty)             
                    if sol.di_type_palette_id.di_qte_cond_inf != 0.0:
                        sol.di_nb_palette = sol.di_nb_colis / sol.di_type_palette_id.di_qte_cond_inf
                    else:
                        sol.di_nb_palette = sol.di_nb_colis
                    sol.di_poin = sol.product_uom_qty * sol.product_id.weight             
                            
                elif sol.di_un_saisie == "COLIS":
                    sol.di_nb_colis = ceil(sol.di_qte_un_saisie)            
                    sol.di_nb_pieces = ceil(sol.product_packaging.di_qte_cond_inf * sol.di_nb_colis)
                    if sol.di_type_palette_id.di_qte_cond_inf !=0.0:                
                        sol.di_nb_palette = sol.di_nb_colis / sol.di_type_palette_id.di_qte_cond_inf
                    else:
                        sol.di_nb_palette = sol.di_nb_colis
                    sol.di_poin = sol.product_uom_qty * sol.product_id.weight             
                                           
                elif sol.di_un_saisie == "PALETTE":            
                    sol.di_nb_palette = sol.di_qte_un_saisie
                    if sol.di_type_palette_id.di_qte_cond_inf!=0.0:
                        sol.di_nb_colis = ceil(sol.di_nb_palette / sol.di_type_palette_id.di_qte_cond_inf)
                    else:
                        sol.di_nb_colis = ceil(sol.di_nb_palette)
                    sol.di_nb_pieces = ceil(sol.product_packaging.di_qte_cond_inf * sol.di_nb_colis)            
                    sol.di_poin = sol.product_uom_qty * sol.product_id.weight             
                      
                elif sol.di_un_saisie == "KG":
    
                    sol.di_poin = sol.di_qte_un_saisie                        
                    if sol.product_packaging.qty !=0.0:
                        sol.di_nb_colis = ceil(sol.product_uom_qty / sol.product_packaging.qty)
                    else:
                        sol.di_nb_colis = ceil(sol.product_uom_qty)
                    if sol.di_type_palette_id.di_qte_cond_inf !=0.0:    
                        sol.di_nb_palette = sol.di_nb_colis / sol.di_type_palette_id.di_qte_cond_inf
                    else:  
                        sol.di_nb_palette = sol.di_nb_colis
                    sol.di_nb_pieces = ceil(sol.product_packaging.di_qte_cond_inf * sol.di_nb_colis)
                      
                else:
                    sol.di_poin = sol.di_qte_un_saisie            
                    sol.product_uom_qty = sol.di_poin
                    if sol.product_packaging.qty !=0.0:
                        sol.di_nb_colis = ceil(sol.product_uom_qty / sol.product_packaging.qty)
                    else:
                        sol.di_nb_colis = ceil(sol.product_uom_qty)
                    if sol.di_type_palette_id.di_qte_cond_inf !=0.0:    
                        sol.di_nb_palette = sol.di_nb_colis / sol.di_type_palette_id.di_qte_cond_inf
                    else:  
                        sol.di_nb_palette = sol.di_nb_colis
                    sol.di_nb_pieces = ceil(sol.product_packaging.di_qte_cond_inf * sol.di_nb_colis)
            else:           
                if sol.product_id.di_get_type_piece().qty != 0.0:
                    sol.di_nb_pieces = ceil(sol.product_uom_qty/sol.product_id.di_get_type_piece().qty)
                else:
                    sol.di_nb_pieces = ceil(sol.product_uom_qty)                                
                if sol.product_packaging.qty != 0.0 :
                    sol.di_nb_colis = ceil(sol.product_uom_qty / sol.product_packaging.qty)
                else:      
                    sol.di_nb_colis = ceil(sol.product_uom_qty)             
                if sol.di_type_palette_id.di_qte_cond_inf != 0.0:
                    sol.di_nb_palette = sol.di_nb_colis / sol.di_type_palette_id.di_qte_cond_inf
                else:
                    sol.di_nb_palette = sol.di_nb_colis
                sol.di_poin = sol.product_uom_qty * sol.product_id.weight 
                sol.di_poib = sol.di_poin + sol.di_tare
            
    @api.multi
    def _check_package(self):    
        # copie standard
        #surcharge pour enlever le contrôle sur le nombre d'unités saisies en fonction du colis choisi    
        return {}
        
    @api.onchange('product_uom_qty', 'product_uom', 'route_id')
    def _onchange_product_id_check_availability(self):
        # copie standard
        #surcharge pour enlever la remise à 0 de product_packaging
        if self.product_id.type == 'product':
            precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
            product = self.product_id.with_context(warehouse=self.order_id.warehouse_id.id,lang=self.order_id.partner_id.lang or self.env.user.lang or 'en_US')
            product_qty = self.product_uom._compute_quantity(self.product_uom_qty, self.product_id.uom_id)
            if float_compare(product.virtual_available, product_qty, precision_digits=precision) == -1:
                is_available = self._check_routing()
                if not is_available:
                    message =  _('You plan to sell %s %s of %s but you only have %s %s available in %s warehouse.') % \
                            (self.product_uom_qty, self.product_uom.name, self.product_id.name, product.virtual_available, product.uom_id.name, self.order_id.warehouse_id.name)
                    # We check if some products are available in other warehouses.
                    if float_compare(product.virtual_available, self.product_id.virtual_available, precision_digits=precision) == -1:
                        message += _('\nThere are %s %s available across all warehouses.\n\n') % \
                                (self.product_id.virtual_available, product.uom_id.name)
                        for warehouse in self.env['stock.warehouse'].search([]):
                            quantity = self.product_id.with_context(warehouse=warehouse.id).virtual_available
                            if quantity > 0:
                                message += "%s: %s %s\n" % (warehouse.name, quantity, self.product_id.uom_id.name)
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
        super(SaleOrderLine, self)._get_to_invoice_qty()
                
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
        super(SaleOrderLine, self)._get_invoice_qty()
  
class SaleOrder(models.Model):
    _inherit = "sale.order"
    di_period_fact = fields.Selection(string="Périodicité de Facturation", related='partner_id.di_period_fact')#,store=True)
    di_regr_fact = fields.Boolean(string="Regroupement sur Facture", related='partner_id.di_regr_fact')#,store=True)
    di_ref = fields.Char(string='Code Tiers', related='partner_id.ref')#,store=True)
    di_livdt = fields.Date(string='Date de livraison', copy=False, help="Date de livraison souhaitée",
                           default=lambda wdate : datetime.today().date()+timedelta(days=1))
    di_prepdt = fields.Date(string='Date de préparation', copy=False, help="Date de préparation",
                           default=lambda wdate : datetime.today().date())    
    di_tournee = fields.Char(string='Tournée',help="Pour regroupement sur les bordereaux de transport")
    di_rangtournee = fields.Char(string='Rang dans la tournée',help="Pour ordre de tri sur les bordereaux de transport")
    di_nbpal = fields.Float(compute='_compute_di_nbpal_nbcol', store=True, digits=dp.get_precision('Product Unit of Measure'))
    di_nbcol = fields.Integer(compute='_compute_di_nbpal_nbcol', store=True)   
    di_nbex = fields.Integer("Nombre exemplaires",help="""Nombre d'exemplaires d'une impression.""",default=0)
    
    @api.multi
    @api.onchange("partner_id")
    def di_onchange_partner(self):
        for order in self:
            if order.partner_id:
                order.di_nbex = order.partner_id.di_nbex_cde
#     di_liste_taxes = fields.Char(compute='_di_compute_taxes',string='Détail des taxes')  
    
#     @api.onchange('order_line')
#     def di_onchange_order_line(self):
#         ligzero = False
#         for ol in self.order_line:
#             if ol.price_total==0.0:
#                 ligzero = True
#         if ligzero:        
#             return {'warning': {'Il exixste une ligne avec montant à 0.': _('Error'), 'message': _('Il exixste une ligne avec montant à 0 !'),},}
    
    @api.multi
    def action_print_invoice(self):
        invoices = self.mapped('invoice_ids')
        for invoice in invoices:
            invoice.invoice_print()
        
    
    @api.multi
    def imprimer_etiquettes(self):         
        param = self.env['di.param'].search([('di_company_id','=',self.env.user.company_id.id)])
        if param.di_label_id and param.di_label_id.file is not None and param.di_label_id.file != "":
            if param.di_printer_id : #and param.di_printer_id.adressip is not None and param.di_printer_id.adressip != "":
                if param.di_printer_id.realname is not None and param.di_printer_id.realname != "":
                    printer = param.di_printer_id.realname
                    label = param.di_label_id.file
                    data=''
                    for so in self:
                        for sol in so.order_line:
                            if sol.product_id.barcode : 
                                barcode = sol.product_id.barcode
                            else:
                                barcode="0000000000000"
                            if sol.move_ids:
                                for sm in sol.move_ids: 
                                    if sm.move_line_ids:
                                        for sml in sm.move_line_ids:
                                            qteform = "000000"
                                            qteform =str(int(sml.qty_done*100)) 
                                            qteform=qteform.rjust(6,'0')            
                                            if sml.lot_id:
                                                informations=[
                                                    ("codeart",sol.product_id.default_code),
                                                    ("des",sol.product_id.product_tmpl_id.name),
                                                    ("qte",sml.qty_done),                                       
                                                    ("codebarre",">802"+barcode+">83102"+qteform+">810"+">6"+sml.lot_id.name),
                                                    ("txtcb","(02)"+barcode+"(3102)"+qteform+"(10)"+sml.lot_id.name),
                                                    ("lot",sml.lot_id.name)
                                                    ]
                                            else:
                                                informations=[
                                                    ("codeart",sol.product_id.default_code),
                                                    ("des",sol.product_id.product_tmpl_id.name),
                                                    ("qte",sml.qty_done),                                        
                                                    ("codebarre",">802"+barcode+">83102"+qteform),
                                                    ("txtcb","(02)"+barcode+"(3102)"+qteform),
                                                    ("lot"," ")                                                                                                                                   
                                                    ]                                                
                                            data =data+ di_ctrl_print.format_data(label, '[', informations)    
#                                             di_ctrl_print.printlabelonwindows(printer,label,'[',informations)
                                    else:
                                        qteform = "000000"
                                        qteform =str(int(sm.product_qty*100)) 
                                        qteform=qteform.rjust(6,'0')
                                        informations=[
                                                    ("codeart",sol.product_id.default_code),
                                                    ("des",sol.product_id.product_tmpl_id.name),
                                                    ("qte",sm.product_qty),                                                                                
                                                    ("codebarre",">802"+barcode+">83102"+qteform),
                                                    ("txtcb","(02)"+barcode+"(3102)"+qteform),
                                                    ("lot"," ")                                                                                                                                                      
                                                    ]   
                                        data =data+ di_ctrl_print.format_data(label, '[', informations)                                             
#                                         di_ctrl_print.printlabelonwindows(printer,label,'[',informations)                                            
                            else:
                                qteform = "000000"
                                qteform =str(int(sol.product_uom_qty*100))
                                qteform=qteform.rjust(6,'0')
                                informations=[
                                    ("codeart",sol.product_id.default_code),
                                    ("des",sol.product_id.product_tmpl_id.name),
                                    ("qte",sol.product_uom_qty),
                                    #("codebarre",sol.product_id.barcode),                                            
                                    ("codebarre",">802"+barcode+">83102"+qteform),
                                    ("txtcb","(02)"+barcode+"(3102)"+qteform),
                                    ("lot"," ")                                                                                                                          
                                    ]
                                data =data+ di_ctrl_print.format_data(label, '[', informations)
#                                 di_ctrl_print.printlabelonwindows(printer,label,'[',informations)
                    di_ctrl_print.printlabelonwindows(printer,data)
                    
#     @api.depends('order_line')                
#     def _di_compute_taxes(self):
#         taxes = self._get_tax_amount_by_group()
#         self.di_liste_taxes = taxes
        
    
    def _amount_by_group(self):
        # copie standard
        for order in self:
            currency = order.currency_id or order.company_id.currency_id
            fmt = partial(formatLang, self.with_context(lang=order.partner_id.lang).env, currency_obj=currency)
            res = {}
            for line in order.order_line:
                # modif de la quantité à prendre en compte
                di_qte_prix = 0.0
                if line.di_un_prix == "PIECE":
                    di_qte_prix = line.di_nb_pieces
                elif line.di_un_prix == "COLIS":
                    di_qte_prix = line.di_nb_colis
                elif line.di_un_prix == "PALETTE":
                    di_qte_prix = line.di_nb_palette
                elif line.di_un_prix == "KG":
                    di_qte_prix = line.di_poin
                elif line.di_un_prix == False or line.di_un_prix == '':
                    di_qte_prix = line.product_uom_qty
                    
                price_reduce = line.price_unit * (1.0 - line.discount / 100.0)
                # Lecture de toutes  les taxes  de la ligne, y compris les taxes spé
                taxes = line.tax_id.compute_all(price_reduce, quantity=di_qte_prix, product=line.product_id, partner=order.partner_shipping_id)['taxes']
#   J'enlève un morceau du standard pour le remplacer afin de pouvoir afficher les taxes spé sur les impressions de commande
#                 for tax in line.tax_id:
#                     group = tax.tax_group_id
#                     res.setdefault(group, {'amount': 0.0, 'base': 0.0})
#                     for t in taxes:
#                         if t['id'] == tax.id or t['id'] in tax.children_tax_ids.ids:
#                             res[group]['amount'] += t['amount']
#                             res[group]['base'] += t['base']
#             res = sorted(res.items(), key=lambda l: l[0].sequence)
#             order.amount_by_group = [(
#                 l[0].name, l[1]['amount'], l[1]['base'],
#                 fmt(l[1]['amount']), fmt(l[1]['base']),
#                 len(res),
#             ) for l in res]

                for tax in taxes: # parcous des taxes trouvées
                    di_taxe = self.env['account.tax'].browse(tax['id'])# recherche de l'enreg de la taxe
                    group = di_taxe.tax_group_id
                    res.setdefault(group, {'amount': 0.0, 'base': 0.0})
                    #ajout des montants par groupe
                    res[group]['amount'] += tax['amount']
                    res[group]['base'] += tax['base']
                    if di_taxe.include_base_amount:
                        base_tax += di_taxe.compute_all(price_reduce + base_tax, quantity=1, product=line.product_id,partner=self.partner_shipping_id)['taxes'][0]['amount']                                            
            res = sorted(res.items(), key=lambda l: l[0].sequence)
            order.amount_by_group = [(
                l[0].name, l[1]['amount'], l[1]['base'],
                fmt(l[1]['amount']), fmt(l[1]['base']),
                len(res),
            ) for l in res]
                   
    
    @api.multi
    @api.onchange('di_livdt')
    def modif_livdt(self):
        if self.di_livdt<datetime.today().date():
            return {'warning': {'Erreur date livraison': _('Error'), 'message': _('La date de livraison ne peut être inférieure à la date du jour !'),},}       
        self.di_prepdt = self.di_livdt + timedelta(days=-1)
        if self.di_prepdt<datetime.today().date():
            self.di_prepdt=datetime.today().date()
        self.requested_date = self.di_livdt
     
    @api.multi
    @api.onchange('di_prepdt')
    def modif_prepdt(self):
        if self.di_prepdt<datetime.today().date():
            return {'warning': {'Erreur date préparation': _('Error'), 'message': _('La date de préparation ne peut être inférieure à la date du jour !'),},}
        self.di_livdt = self.di_prepdt + timedelta(days=1)
        self.requested_date = self.di_livdt
     
    def _force_lines_to_invoice_policy_order(self):
        super(SaleOrder, self)._force_lines_to_invoice_policy_order()
        for line in self.order_line:
            if self.state in ['sale', 'done']:
                line.di_qte_a_facturer_un_saisie = line.di_qte_un_saisie - line.di_qte_un_saisie_fac
            else:
                line.di_qte_a_facturer_un_saisie = 0    
                
    @api.multi
    def di_action_grille_vente(self):
        self.ensure_one()        
         
        view=self.env.ref('difodoo_ventes.di_grille_vente_wiz').id
        #       
      
        ctx= {                
                'di_model':'sale.order',   
                'di_order': self                           
            }
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'name': 'Grille de vente',
            'res_model': 'di.grille.vente.wiz',
            'views': [(view, 'form')],
            'view_id': view,                        
            'target': 'new',
            'multi':'False',
            'id':'di_action_grille_vente_wiz',
            'key2':'client_action_multi',
            'context': ctx            
        }

    @api.model
    def create(self, vals):                                                       
        cde = super(SaleOrder, self).create(vals)
        lines = False
        for order in cde:    
            if order.state == 'draft' :                                    
                lines = self.env['sale.order.line'].search(['&', ('order_id', '=', order.id), ('product_uom_qty', '=', 0.0)])                
                order.write({'order_line': [(2, line.id, False) for line in lines]})
            if order.di_nbex==0: 
                if order.partner_id:                
                    order.write({'di_nbex': order.partner_id.di_nbex_cde})
        return cde
     
#         if lines:
#             view=self.env.ref('difodoo_ventes.di_lig_zero_wiz').id
#             ctx= {                
#                 'order_id': order.id,   
#                 'lines': lines                           
#             }
#             return {
#             'type': 'ir.actions.act_window',
#             'view_type': 'form',
#             'view_mode': 'form',
#             'name': 'Lignes à 0',
#             'res_model': 'di.lig.zero.wiz',
#             'views': [(view, 'form')],
#             'view_id': view,                        
#             'target': 'new',
#             'multi':'False',
#             'id':'di_action_lig_zero_wiz',
#             'key2':'client_action_multi',
#             'context': ctx            
#             }
#         else:    
#             return cde
     
    
    @api.multi
    def write(self, vals):
        res = super(SaleOrder, self).write(vals)   
        lines = False     
        for order in self:    
            if order.state == 'draft' :   
#                 order.di_supp_lig_zero()                                 
                lines = self.env['sale.order.line'].search(['&', ('order_id', '=', order.id), ('product_uom_qty', '=', 0.0)])                               
                super(SaleOrder, order).write({'order_line': [(2, line.id, False) for line in lines]})
        return res
#         if lines:
#             view=self.env.ref('difodoo_ventes.di_lig_zero_wiz').id
#             ctx= {                
#                 'order_id': order.id,   
#                 'lines': lines                           
#             }
#             
#             return {
#             'type': 'ir.actions.act_window',
#             'view_type': 'form',
#             'view_mode': 'form',
#             'name': 'Lignes à 0',
#             'res_model': 'di.lig.zero.wiz',
#             'views': [(view, 'form')],
#             'view_id': view,                        
#             'target': 'new',
#             'multi':'False',
#             'id':'di_action_lig_zero_wiz',
#             'key2':'client_action_multi',
#             'context': ctx            
#             }
#         else:                  
#             return res
    
    
    @api.depends('state', 'order_line.invoice_status')
    def _get_invoiced(self):
        """
        Surcharge pour ne pas mettre le status facturé pour les commandes vides 
        """
        super(SaleOrder, self)._get_invoiced()
        for order in self:                        
            if not order.order_line:
                invoice_status = 'no'                            
                order.update({                
                    'invoice_status': invoice_status
                })
                
                

    @api.multi
    @api.onchange('partner_id')
    def onchange_partner_id(self):
        result=super(SaleOrder, self).onchange_partner_id()
        self.di_tournee = self.partner_id.di_tournee
        self.di_rangtournee = self.partner_id.di_rangtournee         
        return result
    
    @api.depends('order_line')
    def _compute_di_nbpal_nbcol(self):
        for order in self:
            wnbpal = sum(line.di_nb_palette for line in order.order_line)
            wnbcol = sum(line.di_nb_colis for line in order.order_line)
            order.di_nbpal = wnbpal
            order.di_nbcol = ceil(wnbcol)

