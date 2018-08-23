
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
    di_tare         = fields.Float(string='Tare',store=True)
    di_un_prix      = fields.Selection([("PIECE", "Pièce"), ("COLIS", "Colis"),("PALETTE", "Palette"),("KG","Kg")], string="Unité de prix",store=True)

    di_flg_modif_uom = fields.Boolean(store=True)

    di_qte_un_saisie_liv = fields.Float(string='Quantité livrée en unité de saisie')
    di_un_saisie_liv     = fields.Selection([("PIECE", "Pièce"), ("COLIS", "Colis"),("PALETTE", "Palette"),("KG","Kg")], string="Unité de saisie livrée")
    di_type_palette_liv_id  = fields.Many2one('product.packaging', string='Palette livrée') 
    di_nb_pieces_liv     = fields.Integer(string='Nb pièces livrées')
    di_nb_colis_liv      = fields.Integer(string='Nb colis livrés')
    di_nb_palette_liv    = fields.Float(string='Nb palettes livrées')
    di_poin_liv          = fields.Float(string='Poids net livré')
    di_poib_liv          = fields.Float(string='Poids brut livré')
    di_tare_liv          = fields.Float(string='Tare livrée')
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
    
#     di_marge_param = fields.Float(string='% marge',compute='_di_calul_marge_prc',store=True)
#         
#     def di_get_param_by_company_id(self,company_id):    
#         return self.env['di.param'].search(['di_company_id','=',company_id],limit=1) 
    @api.one
    @api.depends('di_marge_prc','company_id.di_param_id.di_seuil_marge_prc')#,'di_param_id.di_seuil_marge_prc')
    def _di_compute_marge_seuil(self):   
        if self.di_marge_prc < self.company_id.di_param_id.di_seuil_marge_prc:     
            self.di_marge_inf_seuil = True
        else:
            self.di_marge_inf_seuil = False
            
    
    @api.one
    @api.depends('price_subtotal','product_uom_qty','purchase_price')
    def _di_calul_marge_prc(self):
        if self.product_uom_qty and self.product_uom_qty != 0.0:
            qte = self.product_uom_qty
        else:
            qte = 1.0
        if self.purchase_price and self.purchase_price !=0.0:
            self.di_marge_prc = (self.price_subtotal/qte - self.purchase_price )*100/self.purchase_price            
        else:
            self.di_marge_prc = self.price_subtotal/qte*100
        
        
    def _get_dernier_prix(self):
        prix = 0.0
        l = self.search(['&', ('product_id', '=', self.product_id.id), ('order_partner_id', '=', self.order_partner_id.id),('order_id.date_order','<',self.order_id.date_order)], limit=1).sorted(key=lambda t: t.order_id.date_order,reverse=True)
        if l.price_unit:
            prix = l.price_unit            
        return prix
    
    @api.one
    @api.depends('product_id','order_partner_id','order_id.date_order')
    def _di_compute_dernier_prix(self):        
        self.di_dern_prix =self._get_dernier_prix()
            
#     @api.model
#     def create(self, vals):         
#         line = False              
#         if vals['product_uom_qty'] and vals['product_uom_qty']!=0.0:
#             line = super(SaleOrderLine, self).create(vals)                                
#         return line
    
              
    def di_recherche_prix_unitaire(self,prixOrig, tiers, article, di_un_prix , qte, date):    
        prixFinal = 0.0       
        prixFinal =self.env["di.tarifs"]._di_get_prix(tiers,article,di_un_prix,qte,date)
        if prixFinal == 0.0:
            prixFinal = prixOrig
#             if prixOrig == 0.0:
#                 raise ValidationError("Le prix unitaire de la ligne est à 0 !")
        return prixFinal                     
    @api.one
    @api.depends('product_id.di_spe_saisissable','product_id','di_qte_un_saisie')
    def _di_compute_spe_saisissable(self):        
        self.di_spe_saisissable =self.product_id.di_spe_saisissable
     

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
                
            vals['price_unit'] = self.di_recherche_prix_unitaire(self.price_unit,self.order_id.partner_id,self.product_id,self.di_un_prix,di_qte_prix,self.order_id.date_order)
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
            self.price_unit = self.di_recherche_prix_unitaire(self.price_unit,self.order_id.partner_id,self.product_id,self.di_un_prix,di_qte_prix,self.order_id.date_order)       
                
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
                line.price_unit = self.di_recherche_prix_unitaire(line.price_unit,line.order_id.partner_id,line.product_id,line.di_un_prix,di_qte_prix,line.order_id.date_order)
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
                
    @api.one
    @api.depends('di_qte_un_saisie', 'di_un_saisie','di_type_palette_id','di_tare','product_packaging')
    def _compute_qte_aff(self):
        #if self.ensure_one():
        
        if self.di_flg_modif_uom == False:
            if self.di_un_saisie == "PIECE":
                self.di_nb_pieces = ceil(self.di_qte_un_saisie)            
                if self.product_packaging.qty != 0.0 :
                    self.di_nb_colis = ceil(self.product_uom_qty / self.product_packaging.qty)
                else:      
                    self.di_nb_colis = ceil(self.product_uom_qty)             
                if self.di_type_palette_id.di_qte_cond_inf != 0.0:
                    self.di_nb_palette = self.di_nb_colis / self.di_type_palette_id.di_qte_cond_inf
                else:
                    self.di_nb_palette = self.di_nb_colis
                self.di_poin = self.product_uom_qty * self.product_id.weight             
                        
            elif self.di_un_saisie == "COLIS":
                self.di_nb_colis = ceil(self.di_qte_un_saisie)            
                self.di_nb_pieces = ceil(self.product_packaging.di_qte_cond_inf * self.di_nb_colis)
                if self.di_type_palette_id.di_qte_cond_inf !=0.0:                
                    self.di_nb_palette = self.di_nb_colis / self.di_type_palette_id.di_qte_cond_inf
                else:
                    self.di_nb_palette = self.di_nb_colis
                self.di_poin = self.product_uom_qty * self.product_id.weight             
                                       
            elif self.di_un_saisie == "PALETTE":            
                self.di_nb_palette = self.di_qte_un_saisie
                if self.di_type_palette_id.di_qte_cond_inf!=0.0:
                    self.di_nb_colis = ceil(self.di_nb_palette / self.di_type_palette_id.di_qte_cond_inf)
                else:
                    self.di_nb_colis = ceil(self.di_nb_palette)
                self.di_nb_pieces = ceil(self.product_packaging.di_qte_cond_inf * self.di_nb_colis)            
                self.di_poin = self.product_uom_qty * self.product_id.weight             
                  
            elif self.di_un_saisie == "KG":

                self.di_poin = self.di_qte_un_saisie                        
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
    @api.multi
    def _get_tax_amount_by_group(self):
        # copie standard
        self.ensure_one()
        res = {}
        for line in self.order_line:
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
            base_tax = 0
#   J'enlève un morceau du standard pour le remplacer afin de pouvoir afficher les taxes spé sur les impressions de commande           
#             for tax in line.tax_id:
#                 group = tax.tax_group_id
#                 res.setdefault(group, {'amount': 0.0, 'base': 0.0})
#                 # FORWARD-PORT UP TO SAAS-17
#                 price_reduce = line.price_unit * (1.0 - line.discount / 100.0)
#                 taxes = tax.compute_all(price_reduce + base_tax, quantity=di_qte_prix,
#                                          product=line.product_id, partner=self.partner_shipping_id)['taxes']
#                 for t in taxes:
#                     res[group]['amount'] += t['amount']
#                     res[group]['base'] += t['base']
#                 if tax.include_base_amount:
#                     base_tax += tax.compute_all(price_reduce + base_tax, quantity=1, product=line.product_id,
#                                                 partner=self.partner_shipping_id)['taxes'][0]['amount']
#         res = sorted(res.items(), key=lambda l: l[0].sequence)
#         res = [(l[0].name, l[1]['amount'], l[1]['base'], len(res)) for l in res]
            price_reduce = line.price_unit * (1.0 - line.discount / 100.0)
            # Lecture de toutes  les taxes  de la ligne, y compris les taxes spé 
            taxes = line.tax_id.compute_all(price_reduce + base_tax, quantity=di_qte_prix,product=line.product_id, partner=self.partner_shipping_id)['taxes']
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
        res = [(l[0].name, l[1]['amount'], l[1]['base'], len(res)) for l in res]   
        return res                         
    
    @api.multi
    @api.onchange('di_livdt')
    def modif_livdt(self):
        if datetime.strptime(self.di_livdt,'%Y-%m-%d').date()<datetime.today().date():
            return {'warning': {'Erreur date livraison': _('Error'), 'message': _('La date de livraison ne peut être inférieure à la date du jour !'),},}       
        self.di_prepdt = datetime.strptime(self.di_livdt,'%Y-%m-%d').date() + timedelta(days=-1)
        if datetime.strptime(self.di_prepdt,'%Y-%m-%d').date()<datetime.today().date():
            self.di_prepdt=datetime.today().date()
        self.requested_date = datetime.strptime(self.di_livdt,'%Y-%m-%d')
     
    @api.multi
    @api.onchange('di_prepdt')
    def modif_prepdt(self):
        if datetime.strptime(self.di_prepdt,'%Y-%m-%d').date()<datetime.today().date():
            return {'warning': {'Erreur date préparation': _('Error'), 'message': _('La date de préparation ne peut être inférieure à la date du jour !'),},}
        self.di_livdt = datetime.strptime(self.di_prepdt,'%Y-%m-%d').date() + timedelta(days=1)
        self.requested_date = datetime.strptime(self.di_livdt,'%Y-%m-%d')
     
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
        status = 'aucun'
        if vals.get('state'):
            if vals['state']=='draft':
                status='draft'
            else:
                status = 'autre'   
        if ((self.state == 'draft' or  not self.state) and status == 'aucun')or(status == 'draft') :            
            lignes_a_zero = False
            if vals.get('order_line'):
                for index,element in enumerate(vals['order_line']):                    
                    dict_line = element[2] # dans element : 0 = action à effectuer , 1=id , 2 = dictionnaire contenant les infos de la ligne
                    
                    di_avec_product_uom_qty = False  # initialisation d'une variable       
                    if dict_line != False:
                        for key in dict_line.items():  # vals est un dictionnaire qui contient les champs modifiés, on va lire les différents enregistrements                      
                            if key[0] == "product_uom_qty":  # si on a modifié la quantité sur une ligne
                                di_avec_product_uom_qty = True
                                break
                                                
                    if di_avec_product_uom_qty:
                        if dict_line['product_uom_qty']==0.0:
                            lignes_a_zero = True
                            break                            
                    else:
                        if element[1]: # si on a un id, on recherche la ligne correspondante. On ne doit pas passer ici en create normalement
                            line = self.env['sale.order.line'].browse(element[1])
                            if line.product_uom_qty ==0.0:
                                lignes_a_zero = True
                                break               
                                 
            if lignes_a_zero == True:
#                 retour_box=messagebox.askyesno("Lignes à 0","Voulez-vous supprimer les lignes à 0 ?")
#                 retour_box=pymsgbox.confirm(text='Voulez-vous supprimer les lignes à 0 ?', title='Lignes à 0', buttons=['Oui', 'Non'])
#                 retour_box = self.env['di.popup.wiz'].afficher_message("Voulez-vous supprimer les lignes à 0 ?",False,True,True,False)
#                 retour_box=ctypes.windll.user32.MessageBoxW(0,"Voulez-vous supprimer les lignes à 0 ?","Lignes à 0",4) #TODO : a modifier
#                 if retour_box == 6:
#                 if retour_box == "oui":
#                 if retour_box == "yes":
#                 if retour_box == "Oui":
                    #Suppression des lignes à 0
                if vals.get('order_line'):
                    for index,element in enumerate(vals['order_line']):
                        dict_line = element[2]
                        
                        di_avec_product_uom_qty = False  # initialisation d'une variable       
                        if dict_line != False:
                            for key in dict_line.items():  # vals est un dictionnaire qui contient les champs modifiés, on va lire les différents enregistrements                      
                                if key[0] == "product_uom_qty":  # si on a modifié la quantité sur une ligne
                                    di_avec_product_uom_qty = True
                                    break
                            
                        if di_avec_product_uom_qty == True:
                            if dict_line['product_uom_qty']==0.0:         
#                                     element[0]=3                                                                   
                                del vals['order_line'][index]       # on retire la ligne de la liste des lignes à enregistrer                                                                     
                        else:
                            line=self.env['sale.order.line'].browse(element[1])
                            if line.product_uom_qty==0.0:
                                del vals['order_line'][index]
#                                     element[0]=3

                                                  
        cde = super(SaleOrder, self).create(vals)   
#         if self.env.context.get('search_default_di_cde') :#and self.order_line:
#             cde.action_confirm()
        return cde
    
    
    
    @api.multi
    def write(self, vals):
        status = 'aucun'
        if vals.get('state'):
            if vals['state']=='draft':
                status='draft'
            else:
                status = 'autre'        
            
        if (self.state == 'draft' and status == 'aucun')or(status == 'draft') :            
            lignes_a_zero = False
            if vals.get('order_line'):
                for index,element in enumerate(vals['order_line']):                    
                    dict_line = element[2]
                    
                    di_avec_product_uom_qty = False  # initialisation d'une variable       
                    if dict_line != False:
                        for key in dict_line.items():  # vals est un dictionnaire qui contient les champs modifiés, on va lire les différents enregistrements                      
                            if key[0] == "product_uom_qty":  # si on a modifié la quantité sur une ligne
                                di_avec_product_uom_qty = True
                                break
                                                
                    if di_avec_product_uom_qty:
                        if dict_line['product_uom_qty']==0.0:
                            lignes_a_zero = True
                            break                            
                    else:
                        if element[1]:
                            line = self.env['sale.order.line'].browse(element[1])
                            if line.product_uom_qty ==0.0:
                                lignes_a_zero = True
                                break               
                                 
#             if lignes_a_zero == False:
#                 if self.order_line:
#                     for line in self.order_line:
#                         if line.product_uom_qty==0.0:
#                             lignes_a_zero = True
#                             break
            if lignes_a_zero == True:
#                 retour_box=messagebox.askyesno("Lignes à 0","Voulez-vous supprimer les lignes à 0 ?")
#                 retour_box=pymsgbox.confirm(text='Voulez-vous supprimer les lignes à 0 ?', title='Lignes à 0', buttons=['Oui', 'Non'])
#                 retour_box = self.env['di.popup.wiz'].afficher_message("Voulez-vous supprimer les lignes à 0 ?",False,True,True,False)
#                 retour_box=ctypes.windll.user32.MessageBoxW(0,"Voulez-vous supprimer les lignes à 0 ?","Lignes à 0",4)#TODO : a modifier
#                 if retour_box == 6:
#                 if retour_box == "oui":
#                 if retour_box == "yes":
#                 if retour_box == "Oui":
                    #Suppression des lignes à 0
                if vals.get('order_line'):
                    for index,element in enumerate(vals['order_line']):
                        di_avec_product_uom_qty = False  # initialisation d'une variable
                        dict_line = element[2]       
                        if dict_line!=False:
                            for key in dict_line.items():  # vals est un dictionnaire qui contient les champs modifiés, on va lire les différents enregistrements                      
                                if key[0] == "product_uom_qty":  # si on a modifié la quantité sur une ligne
                                    di_avec_product_uom_qty = True
                                    break
                            
                        if di_avec_product_uom_qty == True:
                            if dict_line['product_uom_qty']==0.0:  
                                line=self.env['sale.order.line'].browse(element[1]) # recherche de la ligne dans la BDD
                                try: # si on ne peut pas faire .isdigit() c'est que l'id est un entier, donc la ligne est bien dans la BDD alors on passe dans except
                                    line.id.isdigit() # si on peut faire isdigit() alors l'id est un string (ex:virtual_XXX) alors la ligne n'existe pas dans la BDD
                                    # on passe dans le else
                                except:                                                                                                                        
                                    element[0]=3 # change l'action à effectuer : 3=suppression
                                else:                                                                                                                                                                        
                                    del vals['order_line'][index]                                                                            
                        else:
                            line=self.env['sale.order.line'].browse(element[1])
                            if line.product_uom_qty==0.0:
                                element[0]=3
#                                 del vals['order_line'][index]                                                                            
#                     if self.order_line:
#                         for line in self.order_line:
#                             if line.product_uom_qty ==0.0:
#                                 self.order_line.browse(line.id).unlink()
                        
                                
        # confirmer la commande si on a des lignes                        
                               
            # create an analytic account if at least an expense product
            #Création de l'analytique, fait dans la fonction standard. Je ne peux pas appeler la fonction ici
#             if any([expense_policy != 'no' for expense_policy in self.order_line.mapped('product_id.expense_policy')]):
#                 if not self.analytic_account_id:                     
#                     name = self.name                                        
#                     analytic = self.env['account.analytic.account'].create({
#                         'name': name,
#                         'code': self.client_order_ref,
#                         'company_id': self.company_id.id,
#                         'partner_id': self.partner_id.id
#                     })
#                     vals['analytic_account_id']=analytic                    
                                                            
        res = super(SaleOrder, self).write(vals)
        if status == 'aucun':
            for order in self:
                if order.state =='draft':
                    if self.env.context.get('search_default_di_cde') and vals.get('order_line'):                        
        #                 vals['state']='sale'
        #                 vals['confirmation_date']=fields.Datetime.now()    
                        if self.env['ir.config_parameter'].sudo().get_param('sale.auto_done_setting'):
                            state = 'done'
                        else:
                            state='sale'
#                         order.update({                
#                                 'state': state,
#                                 'confirmation_date':fields.Datetime.now()
#                             })                                        
                
#         if vals.get('state'):            
#             self.state = vals['state']
# #         if self.env.context.get('search_default_di_cde') and self.order_line: # boucle dans le write
# #             self.action_confirm()
#             
#         if self.state == 'draft' :
#             for line in self.order_line:
#                 if line.product_uom_qty ==0.0:
#                     self.order_line.browse(line.id).unlink()
#             if self.env.context.get('search_default_di_cde') and self.order_line: # boucle dans le write
#                 self.action_confirm()
# #                     line.order_id.unlink()
        return res
    
    
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
    def _action_confirm(self): 
        # copie standard  pour ne pas confirmer une commande sans ligne
#         if self.order_line :
        super(SaleOrder, self)._action_confirm()
        
        return True

   