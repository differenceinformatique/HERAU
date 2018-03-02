# -*- coding: utf-8 -*-
from odoo import models, fields, api
 
class AccountInvoiceLine(models.Model):
    _inherit = "account.invoice.line"
     
    di_qte_un_saisie = fields.Float(string='Quantité en unité de saisie', store=True)
    di_un_saisie = fields.Selection([("PIECE", "Pièce"), ("COLIS", "Colis"), ("PALETTE", "Palette"), ("POIDS", "Poids")], string="Unité de saisie", store=True)
    di_type_palette_id = fields.Many2one('product.packaging', string='Palette', store=True) 
    di_nb_pieces = fields.Integer(string='Nb pièces', compute="_compute_qte_aff", store=True)
    di_nb_colis = fields.Integer(string='Nb colis' ,compute="_compute_qte_aff", store=True)
    di_nb_palette = fields.Float(string='Nb palettes' ,compute="_compute_qte_aff", store=True)
    di_poin = fields.Float(string='Poids net' ,compute="_compute_qte_aff", store=True)
    di_poib = fields.Float(string='Poids brut', store=True)
    di_tare = fields.Float(string='Tare', store=True)
    di_product_packaging_id = fields.Many2one('product.packaging', string='Package', default=False, store=True)
    di_un_prix      = fields.Selection([("PIECE", "Pièce"), ("COLIS", "Colis"),("PALETTE", "Palette"),("POIDS","Poids")], string="Unité de prix",store=True)
     
     
#     di_qte_un_saisie_init = fields.Float(related="sale_line_id.di_qte_un_saisie")
#     di_un_saisie_init = fields.Selection(related="sale_line_id.di_un_saisie")
#     di_type_palette_init = fields.Many2one(related="sale_line_id.di_type_palette_id") 
#     di_nb_pieces_init = fields.Integer(related="sale_line_id.di_nb_pieces")
#     di_nb_colis_init = fields.Integer(related="sale_line_id.di_nb_colis")
#     di_nb_palette_init = fields.Float(related="sale_line_id.di_nb_palette")
#     di_poin_init = fields.Float(related="sale_line_id.di_poin")
#     di_poib_init = fields.Float(related="sale_line_id.di_poib")
#     di_tare_init = fields.Float(related="sale_line_id.di_tare")
#     product_packaging_init = fields.Many2one(related="sale_line_id.di_product_packaging_id")    
    
 
    @api.one
    @api.depends('price_unit', 'discount', 'invoice_line_tax_ids', 'quantity',
        'product_id', 'invoice_id.partner_id', 'invoice_id.currency_id', 'invoice_id.company_id',
        'invoice_id.date_invoice', 'invoice_id.date','di_qte_un_saisie','di_nb_pieces','di_nb_colis','di_nb_palette','di_poin','di_poib','di_tare','di_un_prix')
    def _compute_price(self):
        currency = self.invoice_id and self.invoice_id.currency_id or None
        price = self.price_unit * (1 - (self.discount or 0.0) / 100.0)
        taxes = False
        di_qte_prix = 0.0
        
        if line.di_un_prix == "PIECE":
            di_qte_prix = self.di_nb_pieces
        elif line.di_un_prix == "COLIS":
            di_qte_prix = self.di_nb_colis
        elif line.di_un_prix == "PALETTE":
            di_qte_prix = self.di_nb_palette
        elif line.di_un_prix == "POIDS":
            di_qte_prix = self.di_poin
        elif line.di_un_prix == False or line.di_un_prix == '':
            di_qte_prix = self.quantity
            
        if self.invoice_line_tax_ids:
            taxes = self.invoice_line_tax_ids.compute_all(price, currency, di_qte_prix, product=self.product_id, partner=self.invoice_id.partner_id)        
        self.price_subtotal = price_subtotal_signed = taxes['total_excluded'] if taxes else di_qte_prix * price
        self.price_total = taxes['total_included'] if taxes else self.price_subtotal
        if self.invoice_id.currency_id and self.invoice_id.currency_id != self.invoice_id.company_id.currency_id:
            price_subtotal_signed = self.invoice_id.currency_id.with_context(date=self.invoice_id._get_currency_rate_date()).compute(price_subtotal_signed, self.invoice_id.company_id.currency_id)
        sign = self.invoice_id.type in ['in_refund', 'out_refund'] and -1 or 1
        self.price_subtotal_signed = price_subtotal_signed * sign
        
        

    @api.one
    @api.depends('di_qte_un_saisie', 'di_un_saisie', 'di_type_palette_id', 'di_poib', 'di_tare', 'di_product_packaging_id')
    def _compute_qte_aff(self):
        #recalcule des quantités non modifiables pour qu'elles soient enregistrées même si on met en readonly dans les masques.        
        if self.di_un_saisie == "PIECE":
            self.di_nb_pieces = self.di_qte_un_saisie            
            if self.di_product_packaging_id.qty != 0.0 :
                self.di_nb_colis = self.quantity / self.di_product_packaging_id.qty
            else:      
                self.di_nb_colis = self.quantity             
            if self.di_type_palette_id.di_qte_cond_inf != 0.0:
                self.di_nb_palette = self.di_nb_colis / self.di_type_palette_id.di_qte_cond_inf
            else:
                self.di_nb_palette = self.di_nb_colis
            self.di_poin = self.quantity * self.product_id.weight             
                    
        elif self.di_un_saisie == "COLIS":
            self.di_nb_colis = self.di_qte_un_saisie            
            self.di_nb_pieces = self.di_product_packaging_id.di_qte_cond_inf * self.di_nb_colis
            if self.di_type_palette_id.di_qte_cond_inf != 0.0:                
                self.di_nb_palette = self.di_nb_colis / self.di_type_palette_id.di_qte_cond_inf
            else:
                self.di_nb_palette = self.di_nb_colis
            self.di_poin = self.quantity * self.product_id.weight             
                                   
        elif self.di_un_saisie == "PALETTE":            
            self.di_nb_palette = self.di_qte_un_saisie
            if self.di_type_palette_id.di_qte_cond_inf != 0.0:
                self.di_nb_colis = self.di_nb_palette / self.di_type_palette_id.di_qte_cond_inf
            else:
                self.di_nb_colis = self.di_nb_palette
            self.di_nb_pieces = self.di_product_packaging_id.di_qte_cond_inf * self.di_nb_colis            
            self.di_poin = self.quantity * self.product_id.weight             
              
        elif self.di_un_saisie == "POIDS":
            self.di_poin = self.di_qte_un_saisie                        
            if self.di_product_packaging_id.qty != 0.0:
                self.di_nb_colis = self.quantity / self.di_product_packaging_id.qty
            else:
                self.di_nb_colis = self.quantity
            if self.di_type_palette_id.di_qte_cond_inf != 0.0:    
                self.di_nb_palette = self.di_nb_colis / self.di_type_palette_id.di_qte_cond_inf
            else:  
                self.di_nb_palette = self.di_nb_colis
            self.di_nb_pieces = self.di_product_packaging_id.di_qte_cond_inf * self.di_nb_colis
              
        else:
            self.di_poin = self.di_qte_un_saisie            
            self.quantity = self.di_poin
            if self.di_product_packaging_id.qty != 0.0:
                self.di_nb_colis = self.quantity / self.di_product_packaging_id.qty
            else:
                self.di_nb_colis = self.quantity
            if self.di_type_palette_id.di_qte_cond_inf != 0.0:    
                self.di_nb_palette = self.di_nb_colis / self.di_type_palette_id.di_qte_cond_inf
            else:  
                self.di_nb_palette = self.di_nb_colis
            self.di_nb_pieces = self.di_product_packaging_id.di_qte_cond_inf * self.di_nb_colis 
     
    @api.multi            
    @api.onchange('product_id')
    def _di_charger_valeur_par_defaut(self):
        if self.ensure_one():
            if self.product_id.id != False:
                self.di_un_saisie = self.product_id.di_un_saisie
                self.di_type_palette_id = self.product_id.di_type_palette_id
                self.di_product_packaging_id = self.product_id.di_type_colis_id
                self.di_un_prix = self.product_id.di_un_prix
                 
    @api.multi            
    @api.onchange('di_qte_un_saisie', 'di_un_saisie', 'di_type_palette_id', 'di_poib', 'di_tare', 'di_product_packaging_id')
    def _di_recalcule_quantites(self):
        if self.ensure_one():
            if self.di_un_saisie == "PIECE":
                self.di_nb_pieces = self.di_qte_un_saisie
                self.quantity = self.product_id.di_get_type_piece().qty * self.di_nb_pieces
                if self.di_product_packaging_id.qty != 0.0 :
                    self.di_nb_colis = self.quantity / self.di_product_packaging_id.qty
                else:      
                    self.di_nb_colis = self.quantity             
                if self.di_type_palette_id.di_qte_cond_inf != 0.0:
                    self.di_nb_palette = self.di_nb_colis / self.di_type_palette_id.di_qte_cond_inf
                else:
                    self.di_nb_palette = self.di_nb_colis
                self.di_poin = self.quantity * self.product_id.weight 
                self.di_poib = self.di_poin + self.di_tare
                       
            elif self.di_un_saisie == "COLIS":
                self.di_nb_colis = self.di_qte_un_saisie
                self.quantity = self.di_product_packaging_id.qty * self.di_nb_colis
                self.di_nb_pieces = self.di_product_packaging_id.di_qte_cond_inf * self.di_nb_colis
                if self.di_type_palette_id.di_qte_cond_inf != 0.0:                
                    self.di_nb_palette = self.di_nb_colis / self.di_type_palette_id.di_qte_cond_inf
                else:
                    self.di_nb_palette = self.di_nb_colis
                self.di_poin = self.quantity * self.product_id.weight 
                self.di_poib = self.di_poin + self.di_tare
                                      
            elif self.di_un_saisie == "PALETTE":            
                self.di_nb_palette = self.di_qte_un_saisie
                if self.di_type_palette_id.di_qte_cond_inf != 0.0:
                    self.di_nb_colis = self.di_nb_palette / self.di_type_palette_id.di_qte_cond_inf
                else:
                    self.di_nb_colis = self.di_nb_palette
                self.di_nb_pieces = self.di_product_packaging_id.di_qte_cond_inf * self.di_nb_colis
                self.quantity = self.di_product_packaging_id.qty * self.di_nb_colis
                self.di_poin = self.quantity * self.product_id.weight 
                self.di_poib = self.di_poin + self.di_tare
                 
            elif self.di_un_saisie == "POIDS":
                self.di_poin = self.di_qte_un_saisie
                self.di_poib = self.di_poin + self.di_tare
                self.quantity = self.di_poin
                if self.di_product_packaging_id.qty != 0.0:
                    self.di_nb_colis = self.quantity / self.di_product_packaging_id.qty
                else:
                    self.di_nb_colis = self.quantity
                if self.di_type_palette_id.di_qte_cond_inf != 0.0:    
                    self.di_nb_palette = self.di_nb_colis / self.di_type_palette_id.di_qte_cond_inf
                else:  
                    self.di_nb_palette = self.di_nb_colis
                self.di_nb_pieces = self.di_product_packaging_id.di_qte_cond_inf * self.di_nb_colis
                 
            else:
                self.di_poin = self.di_qte_un_saisie
                self.di_poib = self.di_poin + self.di_tare
                self.quantity = self.di_poin
                if self.di_product_packaging_id.qty != 0.0:
                    self.di_nb_colis = self.quantity / self.di_product_packaging_id.qty
                else:
                    self.di_nb_colis = self.quantity
                if self.di_type_palette_id.di_qte_cond_inf != 0.0:    
                    self.di_nb_palette = self.di_nb_colis / self.di_type_palette_id.di_qte_cond_inf
                else:  
                    self.di_nb_palette = self.di_nb_colis
                self.di_nb_pieces = self.di_product_packaging_id.di_qte_cond_inf * self.di_nb_colis
               
    @api.model
    def create(self, vals):               
        di_avec_sale_line_ids = False  # initialisation d'une variable       
        di_ctx = dict(self._context or {})  # chargement du contexte
        for key in vals.items():  # vals est un dictionnaire qui contient les champs modifiés, on va lire les différents enregistrements                      
            if key[0] == "sale_line_ids":  # si on a modifié sale_line_id
                di_avec_sale_line_ids = True
        if di_avec_sale_line_ids == True:
            qte_a_fac = 0.0
            poib = 0.0
            for id_ligne in vals["sale_line_ids"][0][2]:
                Disaleorderline = self.env['sale.order.line'].search([('id', '=', id_ligne)], limit=1)                                 
                if Disaleorderline.id != False:               
                    #on attribue par défaut les valeurs de la ligne de commande   
                    vals["di_tare"] = Disaleorderline.di_tare  
                    vals["di_un_saisie"] = Disaleorderline.di_un_saisie
                    vals["di_type_palette_id"] = Disaleorderline.di_type_palette_id.id
                    vals["di_product_packaging_id"] = Disaleorderline.product_packaging.id 
                    vals["di_un_prix"] = Disaleorderline.di_un_prix
                    qte_a_fac += Disaleorderline.di_qte_a_facturer_un_saisie   
                    poib += Disaleorderline.di_poib
                     
            vals["di_qte_un_saisie"] = qte_a_fac
            vals["di_poib"] = poib
  
        res = super(AccountInvoiceLine, self).create(vals)                           
        return res
