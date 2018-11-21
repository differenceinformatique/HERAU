
# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.tools.float_utils import float_compare
import datetime
from math import * 
# from difodoo.addons_gesprim.difodoo_ventes.models.di_outils import di_recherche_prix_unitaire
# from difodoo_ventes import di_outils
# from difodoo.outils import di_outils

class AccountInvoice(models.Model):
    _inherit = 'account.invoice'
    
    di_nbex = fields.Integer("Nombre exemplaires",help="""Nombre d'exemplaires d'une impression.""",default=0)
    
    @api.model
    def create(self,vals):        
        res = super(AccountInvoice, self).create(vals)        
        for invoice in res:   
            if invoice.di_nbex==0: 
                if invoice.partner_id:                
                    invoice.write({'di_nbex': invoice.partner_id.di_nbex_fac})                
        return res
    
    @api.multi
    @api.onchange("partner_id")
    def di_onchange_partner(self):
        for fac in self:
            if fac.partner_id:
                fac.di_nbex = fac.partner_id.di_nbex_fac
    
    @api.multi
    def _invoice_line_tax_values(self):
        # copie standard
        self.ensure_one()
        tax_datas = {}
        TAX = self.env['account.tax']

        for line in self.mapped('invoice_line_ids'):
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
                di_qte_prix = line.quantity
                
            price_unit = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
            tax_lines = line.invoice_line_tax_ids.compute_all(price_unit, line.invoice_id.currency_id, di_qte_prix, line.product_id, line.invoice_id.partner_id)['taxes']
            for tax_line in tax_lines:
                tax_line['tag_ids'] = TAX.browse(tax_line['id']).tag_ids.ids
            tax_datas[line.id] = tax_lines
        return tax_datas
   
    
    @api.multi
    def get_taxes_values(self):  
        # copie standard          
        tax_grouped = {}
        for line in self.invoice_line_ids:
            if not line.account_id:
                continue
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
                di_qte_prix = line.quantity
                                
            price_unit = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
#             taxes = line.invoice_line_tax_ids.compute_all(price_unit, self.currency_id, line.quantity, line.product_id, self.partner_id)['taxes']
            taxes = line.invoice_line_tax_ids.compute_all(price_unit, self.currency_id, di_qte_prix, line.product_id, self.partner_id)['taxes']
            for tax in taxes:
                val = self._prepare_tax_line_vals(line, tax)
                key = self.env['account.tax'].browse(tax['id']).get_grouping_key(val)

                if key not in tax_grouped:
                    tax_grouped[key] = val
                else:
                    tax_grouped[key]['amount'] += val['amount']
                    tax_grouped[key]['base'] += val['base']
        return tax_grouped
    
    
    def _prepare_invoice_line_from_po_line(self, line):
        # copie standard
        #Copie du standard pour ajouter des éléments dans data
        if line.product_id.purchase_method == 'purchase':
            qty = line.product_qty - line.qty_invoiced
            di_qte_un_saisie = line.di_qte_un_saisie - line.di_qte_un_saisie_fac
            di_poib = line.di_poib - line.di_poib_fac            
        #ajout difodoo
        else:
            qty = line.qty_received - line.qty_invoiced
            di_qte_un_saisie = line.di_qte_un_saisie_liv - line.di_qte_un_saisie_fac
            di_poib = line.di_poib_liv - line.di_poib_fac
        #ajout difodoo
        if float_compare(qty, 0.0, precision_rounding=line.product_uom.rounding) <= 0:
            qty = 0.0
        taxes = line.taxes_id
        invoice_line_tax_ids = line.order_id.fiscal_position_id.map_tax(taxes)
        invoice_line = self.env['account.invoice.line']
        data = {
            'purchase_line_id': line.id,
            'name': line.order_id.name+': '+line.name,
            'origin': line.order_id.origin,
            'uom_id': line.product_uom.id,
            'product_id': line.product_id.id,
            'account_id': invoice_line.with_context({'journal_id': self.journal_id.id, 'type': 'in_invoice'})._default_account(),
            'price_unit': line.order_id.currency_id.with_context(date=self.date_invoice).compute(line.price_unit, self.currency_id, round=False),
            'quantity': qty,
            'discount': 0.0,
            'account_analytic_id': line.account_analytic_id.id,
            'analytic_tag_ids': line.analytic_tag_ids.ids,
            'invoice_line_tax_ids': invoice_line_tax_ids.ids,
            #Ajout des éléments difodoo
            'di_tare':line.di_tare,  
            'di_un_saisie':line.di_un_saisie,
            'di_type_palette_id':line.di_type_palette_id,
            'di_product_packaging_id':line.product_packaging,
            'di_un_prix':line.di_un_prix,
            'di_qte_un_saisie':di_qte_un_saisie,
            'di_poib':di_poib
                               
        }
        account = invoice_line.get_invoice_line_account('in_invoice', line.product_id, line.order_id.fiscal_position_id, self.env.user.company_id)
        if account:
            data['account_id'] = account.id
        return data
     
class AccountInvoiceLine(models.Model):
    _inherit = "account.invoice.line"
    
    modifparprg = False
     
    di_qte_un_saisie = fields.Float(string='Quantité en unité de saisie', store=True)
    di_un_saisie = fields.Selection([("PIECE", "Pièce"), ("COLIS", "Colis"), ("PALETTE", "Palette"), ("KG", "Kg")], string="Unité de saisie", store=True)
    di_type_palette_id = fields.Many2one('product.packaging', string='Palette', store=True) 
    di_nb_pieces = fields.Integer(string='Nb pièces', compute="_compute_qte_aff", store=True)
    di_nb_colis = fields.Integer(string='Nb colis' ,compute="_compute_qte_aff", store=True)
    di_nb_palette = fields.Float(string='Nb palettes' ,compute="_compute_qte_aff", store=True)
    di_poin = fields.Float(string='Poids net' ,compute="_compute_qte_aff", store=True)
    di_poib = fields.Float(string='Poids brut', store=True)
    di_tare = fields.Float(string='Tare', store=True)#,compute="_compute_tare")
    di_product_packaging_id = fields.Many2one('product.packaging', string='Package', default=False, store=True)
    di_un_prix      = fields.Selection([("PIECE", "Pièce"), ("COLIS", "Colis"),("PALETTE", "Palette"),("KG","Kg")], string="Unité de prix",store=True)
    di_flg_modif_uom = fields.Boolean(default=False)
    
    di_spe_saisissable = fields.Boolean(string='Champs spé saisissables',default=False,compute='_di_compute_spe_saisissable',store=True)
    
    @api.multi
    @api.onchange('di_type_palette_id','di_product_packaging_id','di_nb_colis','di_nb_palette')
    def _compute_tare(self):        
        self.di_tare = (self.di_type_palette_id.di_poids * self.di_nb_palette) + (self.di_product_packaging_id.di_poids * self.di_nb_colis)
        
    def di_recherche_prix_unitaire(self,prixOrig, tiers, article, di_un_prix , qte, date,typecol,typepal):    
        prixFinal = 0.0       
        prixFinal =self.env["di.tarifs"]._di_get_prix(tiers,article,di_un_prix,qte,date,typecol,typepal)
        if prixFinal == 0.0:
            prixFinal = prixOrig
#             if prixOrig == 0.0:
#                 raise Warning("Le prix unitaire de la ligne est à 0 !")
        return prixFinal 
    
    @api.multi
    @api.depends('product_id.di_spe_saisissable')
    def _di_compute_spe_saisissable(self):
        for aol in self:        
            aol.di_spe_saisissable =aol.product_id.di_spe_saisissable
     
 
 # n'existe plus en v12
#     @api.depends('price_unit', 'discount', 'invoice_line_tax_ids', 'quantity',
#         'product_id', 'invoice_id.partner_id', 'invoice_id.currency_id', 'invoice_id.company_id',
#         'invoice_id.date_invoice')
#     def _compute_total_price(self):
#         for line in self:
#             # modif de la quantité à prendre en compte
#             di_qte_prix = 0.0
#             if line.di_un_prix == "PIECE":
#                 di_qte_prix = line.di_nb_pieces
#             elif line.di_un_prix == "COLIS":
#                 di_qte_prix = line.di_nb_colis
#             elif line.di_un_prix == "PALETTE":
#                 di_qte_prix = line.di_nb_palette
#             elif line.di_un_prix == "KG":
#                 di_qte_prix = line.di_poin
#             elif line.di_un_prix == False or line.di_un_prix == '':
#                 di_qte_prix = line.quantity
#             price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
#             taxes = line.invoice_line_tax_ids.compute_all(price, line.invoice_id.currency_id, di_qte_prix, product=line.product_id, partner=line.invoice_id.partner_id)
#             line.price_total = taxes['total_included']

    
    
    @api.one # SC je garde api.one car c'est une copie du standard
    @api.depends('price_unit', 'discount', 'invoice_line_tax_ids', 'quantity',
        'product_id', 'invoice_id.partner_id', 'invoice_id.currency_id', 'invoice_id.company_id',
        'invoice_id.date_invoice', 'invoice_id.date','di_qte_un_saisie','di_nb_pieces','di_nb_colis','di_nb_palette','di_poin','di_poib','di_tare','di_un_prix')
    def _compute_price(self):
        # copie standard
        currency = self.invoice_id and self.invoice_id.currency_id or None
        price = self.price_unit * (1 - (self.discount or 0.0) / 100.0)
        taxes = False
        
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
            di_qte_prix = self.quantity
            
        if self.invoice_line_tax_ids:
            taxes = self.invoice_line_tax_ids.compute_all(price, currency, di_qte_prix, product=self.product_id, partner=self.invoice_id.partner_id)        
        self.price_subtotal = price_subtotal_signed = taxes['total_excluded'] if taxes else di_qte_prix * price
        self.price_total = taxes['total_included'] if taxes else self.price_subtotal
        if self.invoice_id.currency_id and self.invoice_id.currency_id != self.invoice_id.company_id.currency_id:
            currency = self.invoice_id.currency_id
            date = self.invoice_id._get_currency_rate_date()
            price_subtotal_signed = currency._convert(price_subtotal_signed, self.invoice_id.company_id.currency_id, self.company_id or self.env.user.company_id, date or fields.Date.today())
        sign = self.invoice_id.type in ['in_refund', 'out_refund'] and -1 or 1
        self.price_subtotal_signed = price_subtotal_signed * sign

        
    @api.multi
    @api.onchange('product_id','invoice_id.partner_id','invoice_id.date','di_un_prix','di_qte_un_saisie','di_nb_pieces','di_nb_colis','di_nb_palette','di_poin','di_poib','di_tare','quantity')
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
                di_qte_prix = line.quantity             
            if line.product_id.id != False and line.di_un_prix:       
                line.price_unit = self.di_recherche_prix_unitaire(line.price_unit,line.invoice_id.partner_id,line.product_id,line.di_un_prix,di_qte_prix,line.invoice_id.date,line.product_packaging,line.di_type_palette_id)            
     
    @api.multi            
    @api.onchange('product_id')
    def _di_charger_valeur_par_defaut(self):
        if self.ensure_one():
            if self.partner_id and self.product_id:
                ref = self.env['di.ref.art.tiers'].search([('di_partner_id','=',self.partner_id.id),('di_product_id','=',self.product_id.id)],limit=1)
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
    @api.onchange('di_poib')
    def _di_recalcule_tare(self):
        if self.ensure_one():
            self.di_tare = self.di_poib - self.di_poin            
                 
                 
                 
    @api.multi    
    @api.onchange('quantity')
    def _di_modif_qte_un_mesure(self):
        if self.ensure_one():
            if AccountInvoiceLine.modifparprg == False:
                if self.uom_id:
                    if self.uom_id.name.lower() == 'kg':
                        self.di_poin=self.quantity * self.product_id.weight
                        self.di_poib = self.di_poin + self.di_tare
                    elif self.uom_id.name.lower() != 'kg':    
                        if self.product_id.di_get_type_piece().qty != 0.0:
                            self.di_nb_pieces = ceil(self.quantity/self.product_id.di_get_type_piece().qty)
                        else:
                            self.di_nb_pieces = ceil(self.quantity)                                
                        if self.di_product_packaging_id.qty != 0.0 :
                            self.di_nb_colis = ceil(self.quantity / self.di_product_packaging_id.qty)
                        else:      
                            self.di_nb_colis = ceil(self.quantity)             
                        if self.di_type_palette_id.di_qte_cond_inf != 0.0:
                            self.di_nb_palette = self.di_nb_colis / self.di_type_palette_id.di_qte_cond_inf
                        else:
                            self.di_nb_palette = self.di_nb_colis
                        self.di_poin = self.quantity * self.product_id.weight 
                        self.di_poib = self.di_poin + self.di_tare
                    self.di_flg_modif_uom = True
            AccountInvoiceLine.modifparprg=False
            
            
    @api.multi            
    @api.onchange('di_qte_un_saisie', 'di_un_saisie', 'di_type_palette_id', 'di_tare', 'di_product_packaging_id')
    def _di_recalcule_quantites(self):
        if self.ensure_one():
            if self.di_flg_modif_uom == False:
                if self.di_un_saisie == "PIECE":
                    self.di_nb_pieces = ceil(self.di_qte_un_saisie)
                    self.quantity = self.product_id.di_get_type_piece().qty * self.di_nb_pieces
                    if self.di_product_packaging_id.qty != 0.0 :
                        self.di_nb_colis = ceil(self.quantity / self.di_product_packaging_id.qty)
                    else:      
                        self.di_nb_colis = ceil(self.quantity)             
                    if self.di_type_palette_id.di_qte_cond_inf != 0.0:
                        self.di_nb_palette = self.di_nb_colis / self.di_type_palette_id.di_qte_cond_inf
                    else:
                        self.di_nb_palette = self.di_nb_colis
                    self.di_poin = self.quantity * self.product_id.weight 
                    self.di_poib = self.di_poin + self.di_tare
                           
                elif self.di_un_saisie == "COLIS":
                    self.di_nb_colis = ceil(self.di_qte_un_saisie)
                    self.quantity = self.di_product_packaging_id.qty * self.di_nb_colis
                    self.di_nb_pieces = ceil(self.di_product_packaging_id.di_qte_cond_inf * self.di_nb_colis)
                    if self.di_type_palette_id.di_qte_cond_inf != 0.0:                
                        self.di_nb_palette = self.di_nb_colis / self.di_type_palette_id.di_qte_cond_inf
                    else:
                        self.di_nb_palette = self.di_nb_colis
                    self.di_poin = self.quantity * self.product_id.weight 
                    self.di_poib = self.di_poin + self.di_tare
                                          
                elif self.di_un_saisie == "PALETTE":            
                    self.di_nb_palette = self.di_qte_un_saisie
                    if self.di_type_palette_id.di_qte_cond_inf != 0.0:
                        self.di_nb_colis = ceil(self.di_nb_palette / self.di_type_palette_id.di_qte_cond_inf)
                    else:
                        self.di_nb_colis = ceil(self.di_nb_palette)
                    self.di_nb_pieces = ceil(self.di_product_packaging_id.di_qte_cond_inf * self.di_nb_colis)
                    self.quantity = self.di_product_packaging_id.qty * self.di_nb_colis
                    self.di_poin = self.quantity * self.product_id.weight 
                    self.di_poib = self.di_poin + self.di_tare
                     
                elif self.di_un_saisie == "KG":
                    self.di_poin = self.di_qte_un_saisie
                    self.di_poib = self.di_poin + self.di_tare
                    self.quantity = self.di_poin
                    if self.di_product_packaging_id.qty != 0.0:
                        self.di_nb_colis = ceil(self.quantity / self.di_product_packaging_id.qty)
                    else:
                        self.di_nb_colis = ceil(self.quantity)
                    if self.di_type_palette_id.di_qte_cond_inf != 0.0:    
                        self.di_nb_palette = self.di_nb_colis / self.di_type_palette_id.di_qte_cond_inf
                    else:  
                        self.di_nb_palette = self.di_nb_colis
                    self.di_nb_pieces = ceil(self.di_product_packaging_id.di_qte_cond_inf * self.di_nb_colis)
                     
                else:
                    self.di_poin = self.di_qte_un_saisie
                    self.di_poib = self.di_poin + self.di_tare
                    self.quantity = self.di_poin
                    if self.di_product_packaging_id.qty != 0.0:
                        self.di_nb_colis = ceil(self.quantity / self.di_product_packaging_id.qty)
                    else:
                        self.di_nb_colis = ceil(self.quantity)
                    if self.di_type_palette_id.di_qte_cond_inf != 0.0:    
                        self.di_nb_palette = self.di_nb_colis / self.di_type_palette_id.di_qte_cond_inf
                    else:  
                        self.di_nb_palette = self.di_nb_colis
                    self.di_nb_pieces = ceil(self.di_product_packaging_id.di_qte_cond_inf * self.di_nb_colis)
                    
    @api.multi
    @api.depends('di_qte_un_saisie', 'di_un_saisie', 'di_type_palette_id', 'di_tare', 'di_product_packaging_id')
    def _compute_qte_aff(self):
        #recalcule des quantités non modifiables pour qu'elles soient enregistrées même si on met en readonly dans les masques.
        for aol in self:
            if aol.di_flg_modif_uom == False:        
                if aol.di_un_saisie == "PIECE":
                    aol.di_nb_pieces = ceil(aol.di_qte_un_saisie)            
                    if aol.di_product_packaging_id.qty != 0.0 :
                        aol.di_nb_colis = ceil(aol.quantity / aol.di_product_packaging_id.qty)
                    else:      
                        aol.di_nb_colis = ceil(aol.quantity)             
                    if aol.di_type_palette_id.di_qte_cond_inf != 0.0:
                        aol.di_nb_palette = aol.di_nb_colis / aol.di_type_palette_id.di_qte_cond_inf
                    else:
                        aol.di_nb_palette = aol.di_nb_colis
                    aol.di_poin = aol.quantity * aol.product_id.weight             
                            
                elif aol.di_un_saisie == "COLIS":
                    aol.di_nb_colis = ceil(aol.di_qte_un_saisie)            
                    aol.di_nb_pieces = ceil(aol.di_product_packaging_id.di_qte_cond_inf * aol.di_nb_colis)
                    if aol.di_type_palette_id.di_qte_cond_inf != 0.0:                
                        aol.di_nb_palette = aol.di_nb_colis / aol.di_type_palette_id.di_qte_cond_inf
                    else:
                        aol.di_nb_palette = aol.di_nb_colis
                    aol.di_poin = aol.quantity * aol.product_id.weight             
                                           
                elif aol.di_un_saisie == "PALETTE":            
                    aol.di_nb_palette = aol.di_qte_un_saisie
                    if aol.di_type_palette_id.di_qte_cond_inf != 0.0:
                        aol.di_nb_colis = ceil(aol.di_nb_palette / aol.di_type_palette_id.di_qte_cond_inf)
                    else:
                        aol.di_nb_colis = ceil(aol.di_nb_palette)
                    aol.di_nb_pieces = ceil(aol.di_product_packaging_id.di_qte_cond_inf * aol.di_nb_colis)            
                    aol.di_poin = aol.quantity * aol.product_id.weight             
                      
                elif aol.di_un_saisie == "KG":
                    aol.di_poin = aol.di_qte_un_saisie                        
                    if aol.di_product_packaging_id.qty != 0.0:
                        aol.di_nb_colis = ceil(aol.quantity / aol.di_product_packaging_id.qty)
                    else:
                        aol.di_nb_colis = ceil(aol.quantity)
                    if aol.di_type_palette_id.di_qte_cond_inf != 0.0:    
                        aol.di_nb_palette = aol.di_nb_colis / aol.di_type_palette_id.di_qte_cond_inf
                    else:  
                        aol.di_nb_palette = aol.di_nb_colis
                    aol.di_nb_pieces = ceil(aol.di_product_packaging_id.di_qte_cond_inf * aol.di_nb_colis)
                      
                else:
                    aol.di_poin = aol.di_qte_un_saisie            
                    aol.quantity = aol.di_poin
                    if aol.di_product_packaging_id.qty != 0.0:
                        aol.di_nb_colis = ceil(aol.quantity / aol.di_product_packaging_id.qty)
                    else:
                        aol.di_nb_colis = ceil(aol.quantity)
                    if aol.di_type_palette_id.di_qte_cond_inf != 0.0:    
                        aol.di_nb_palette = aol.di_nb_colis / aol.di_type_palette_id.di_qte_cond_inf
                    else:  
                        aol.di_nb_palette = aol.di_nb_colis
                    aol.di_nb_pieces = ceil(aol.di_product_packaging_id.di_qte_cond_inf * aol.di_nb_colis) 
            else:           
                if aol.product_id.di_get_type_piece().qty != 0.0:
                    aol.di_nb_pieces = ceil(aol.quantity/aol.product_id.di_get_type_piece().qty)
                else:
                    aol.di_nb_pieces = ceil(aol.quantity)                                
                if aol.di_product_packaging_id.qty != 0.0 :
                    aol.di_nb_colis = ceil(aol.quantity / aol.di_product_packaging_id.qty)
                else:      
                    aol.di_nb_colis = ceil(aol.quantity)             
                if aol.di_type_palette_id.di_qte_cond_inf != 0.0:
                    aol.di_nb_palette = aol.di_nb_colis / aol.di_type_palette_id.di_qte_cond_inf
                else:
                    aol.di_nb_palette = aol.di_nb_colis
                aol.di_poin = aol.quantity * aol.product_id.weight 
                aol.di_poib = aol.di_poin + aol.di_tare
               
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
                    vals["di_flg_modif_uom"]=Disaleorderline.di_flg_modif_uom
                    qte_a_fac += Disaleorderline.di_qte_a_facturer_un_saisie   
                    poib += Disaleorderline.di_poib
                     
            vals["di_qte_un_saisie"] = qte_a_fac
            vals["di_poib"] = poib            
            
        di_avec_purchase_line_ids = False  # initialisation d'une variable       
        di_ctx = dict(self._context or {})  # chargement du contexte
        for key in vals.items():  # vals est un dictionnaire qui contient les champs modifiés, on va lire les différents enregistrements                      
            if key[0] == "purchase_line_ids":  # si on a modifié sale_line_id
                di_avec_purchase_line_ids = True
        if di_avec_purchase_line_ids == True:
            qte_a_fac = 0.0
            poib = 0.0
            for id_ligne in vals["purchase_line_ids"][0][2]:
                Dipurchaseorderline = self.env['purchase.order.line'].search([('id', '=', id_ligne)], limit=1)                                 
                if Dipurchaseorderline.id != False:               
                    #on attribue par défaut les valeurs de la ligne de commande   
                    vals["di_tare"] = Dipurchaseorderline.di_tare  
                    vals["di_un_saisie"] = Dipurchaseorderline.di_un_saisie
                    vals["di_type_palette_id"] = Dipurchaseorderline.di_type_palette_id.id
                    vals["di_product_packaging_id"] = Dipurchaseorderline.product_packaging.id 
                    vals["di_un_prix"] = Dipurchaseorderline.di_un_prix
                    qte_a_fac += Dipurchaseorderline.di_qte_un_saisie   
                    poib += Dipurchaseorderline.di_poib
                     
            vals["di_qte_un_saisie"] = qte_a_fac
            vals["di_poib"] = poib
  
        res = super(AccountInvoiceLine, self).create(vals)                           
        return res



class AccountTax(models.Model):
    _inherit = 'account.tax'
        
    di_taxe_id = fields.Many2one('account.tax', string='Taxe sur la taxe',help="""Permet par exemple d'affecter de la TVA sur l'interfel """)
    
    @api.multi
    def compute_all(self, price_unit, currency=None, quantity=1.0, product=None, partner=None):
        # copie standard
        """ Returns all information required to apply taxes (in self + their children in case of a tax goup).
            We consider the sequence of the parent for group of taxes.
                Eg. considering letters as taxes and alphabetic order as sequence :
                [G, B([A, D, F]), E, C] will be computed as [A, D, F, C, E, G]

        RETURN: {
            'total_excluded': 0.0,    # Total without taxes
            'total_included': 0.0,    # Total with taxes
            'taxes': [{               # One dict for each tax in self and their children
                'id': int,
                'name': str,
                'amount': float,
                'sequence': int,
                'account_id': int,
                'refund_account_id': int,
                'analytic': boolean,
            }]
        } """
        if len(self) == 0:
            company_id = self.env.user.company_id
        else:
            company_id = self[0].company_id
        if not currency:
            currency = company_id.currency_id
        taxes = []
        # By default, for each tax, tax amount will first be computed
        # and rounded at the 'Account' decimal precision for each
        # PO/SO/invoice line and then these rounded amounts will be
        # summed, leading to the total amount for that tax. But, if the
        # company has tax_calculation_rounding_method = round_globally,
        # we still follow the same method, but we use a much larger
        # precision when we round the tax amount for each line (we use
        # the 'Account' decimal precision + 5), and that way it's like
        # rounding after the sum of the tax amounts of each line
        prec = currency.decimal_places

        # In some cases, it is necessary to force/prevent the rounding of the tax and the total
        # amounts. For example, in SO/PO line, we don't want to round the price unit at the
        # precision of the currency.
        # The context key 'round' allows to force the standard behavior.
        round_tax = False if company_id.tax_calculation_rounding_method == 'round_globally' else True
        round_total = True
        if 'round' in self.env.context:
            round_tax = bool(self.env.context['round'])
            round_total = bool(self.env.context['round'])

        if not round_tax:
            prec += 5

        base_values = self.env.context.get('base_values')
        if not base_values:
            total_excluded = total_included = base = round(price_unit * quantity, prec)
        else:
            total_excluded, total_included, base = base_values

        # Sorting key is mandatory in this case. When no key is provided, sorted() will perform a
        # search. However, the search method is overridden in account.tax in order to add a domain
        # depending on the context. This domain might filter out some taxes from self, e.g. in the
        # case of group taxes.
        
        for tax in self.sorted(key=lambda r: r.sequence):
            price_include = self._context.get('force_price_include', tax.price_include)
            if tax.amount_type == 'group':
                children = tax.children_tax_ids.with_context(base_values=(total_excluded, total_included, base))
                ret = children.compute_all(price_unit, currency, quantity, product, partner)
                total_excluded = ret['total_excluded']
                base = ret['base'] if tax.include_base_amount else base
                total_included = ret['total_included']
                tax_amount = total_included - total_excluded
                taxes += ret['taxes']
                continue

            tax_amount = tax._compute_amount(base, price_unit, quantity, product, partner)
            if not round_tax:
                tax_amount = round(tax_amount, prec)
            else:
                tax_amount = currency.round(tax_amount)

            if price_include:
                total_excluded -= tax_amount
                base -= tax_amount
            else:
                total_included += tax_amount

            # Keep base amount used for the current tax
            tax_base = base

            if tax.include_base_amount:
                base += tax_amount

            taxes.append({
                'id': tax.id,
                'name': tax.with_context(**{'lang': partner.lang} if partner else {}).name,
                'amount': tax_amount,
                'base': tax_base,
                'sequence': tax.sequence,
                'account_id': tax.account_id.id,
                'refund_account_id': tax.refund_account_id.id,
                'analytic': tax.analytic,
                'price_include': tax.price_include, 
                'tax_exigibility': tax.tax_exigibility,               
            })
             
            # spé pour affecter une taxe sur une autre taxe
            if tax.di_taxe_id:
                di_tax_amount = tax.di_taxe_id._compute_amount(tax_amount, tax_amount, 1.0, product, partner)
                if not round_tax:
                    di_tax_amount = round(di_tax_amount, prec)
                else:
                    di_tax_amount = currency.round(di_tax_amount)                
                taxes.append({
                    'id': tax.di_taxe_id.id,
                    'name': tax.di_taxe_id.with_context(**{'lang': partner.lang} if partner else {}).name,
                    'amount': di_tax_amount,
                    'base': tax_amount,
                    'sequence': tax.di_taxe_id.sequence,
                    'account_id': tax.di_taxe_id.account_id.id,
                    'refund_account_id': tax.di_taxe_id.refund_account_id.id,
                    'analytic': tax.di_taxe_id.analytic,
                    'price_include': tax.di_taxe_id.price_include, 
                    'tax_exigibility': tax.di_taxe_id.tax_exigibility,                   
                })
                
                #fin spé
                

        return {
            'taxes': sorted(taxes, key=lambda k: k['sequence']),
            'total_excluded': currency.round(total_excluded) if round_total else total_excluded,
            'total_included': currency.round(total_included) if round_total else total_included,
            'base': base,
        }