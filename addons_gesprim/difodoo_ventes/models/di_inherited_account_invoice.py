
# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.tools.float_utils import float_compare
from odoo.tools import float_utils
import datetime
from math import * 
# from difodoo.addons_gesprim.difodoo_ventes.models.di_outils import di_recherche_prix_unitaire
# from difodoo_ventes import di_outils
# from difodoo.outils import di_outils


# mapping invoice type to refund type
TYPE2REFUND = {
    'out_invoice': 'out_refund',        # Customer Invoice
    'in_invoice': 'in_refund',          # Vendor Bill
    'out_refund': 'out_invoice',        # Customer Credit Note
    'in_refund': 'in_invoice',          # Vendor Credit Note
}
class AccountInvoice(models.Model):
    _inherit = 'account.invoice'
    
    di_nbex = fields.Integer("Nombre exemplaires",help="""Nombre d'exemplaires d'une impression.""",default=0)    
    di_nb_lig = fields.Integer(string='Nb lignes saisies', compute="_compute_nb_lignes")    
    di_rlvno = fields.Integer("Numéro de relevé", default=0)
    di_amount_tax_signed = fields.Monetary(string='Tax Amount in Invoice Currency', currency_field='currency_id', store=True, readonly=True, compute='_compute_amount',
                                           help="Tax amount in the currency of the invoice, negative for credit notes.")
    di_amount_untaxed_signed = fields.Monetary(string='Total in Invoice Currency', currency_field='currency_id', store=True, readonly=True, compute='_compute_amount',    # en standard donnée en devise dossier
                                             help="Total amount in the currency of the invoice, negative for credit notes.")
    di_period_fact = fields.Selection([("DEMANDE", "Demande"), ("SEMAINE", "Semaine"),("DECADE", "Décade"),("QUINZAINE","Quinzaine"),("MOIS","Mois")]
                                     ,related='partner_id.di_period_fact_aff', string="Périodicité de Facturation", help="Permet de filtrer lors de la facturation")

    di_date_piece_orig = fields.Date(string="Date pièece origine",compute="_compute_date_piece_orig" )#,store=True)
    
#     di_mois = fields.Integer("Mois",compute='_compute_mois')
         
    @api.depends("date_invoice")
    def _compute_mois(self):
        for invoice in self:
           invoice.di_mois = invoice.date_invoice.month
    
    
    @api.model
    def _prepare_refund(self, invoice, date_invoice=None, date=None, description=None, journal_id=None):
        """ Prepare the dict of values to create the new credit note from the invoice.
            This method may be overridden to implement custom
            credit note generation (making sure to call super() to establish
            a clean extension chain).

            :param record invoice: invoice as credit note
            :param string date_invoice: credit note creation date from the wizard
            :param integer date: force date from the wizard
            :param string description: description of the credit note from the wizard
            :param integer journal_id: account.journal from the wizard
            :return: dict of value to create() the credit note
        """
        # copie standard
        values = {}
        for field in self._get_refund_copy_fields():
            if invoice._fields[field].type == 'many2one':
                values[field] = invoice[field].id
            else:
                values[field] = invoice[field] or False

        values['invoice_line_ids'] = self._refund_cleanup_lines(invoice.invoice_line_ids)

        tax_lines = invoice.tax_line_ids
        taxes_to_change = {
            line.tax_id.id: line.tax_id.refund_account_id.id
            for line in tax_lines.filtered(lambda l: l.tax_id.refund_account_id != l.tax_id.account_id)
        }
        cleaned_tax_lines = self._refund_cleanup_lines(tax_lines)
        values['tax_line_ids'] = self._refund_tax_lines_account_change(cleaned_tax_lines, taxes_to_change)

        if journal_id:
            journal = self.env['account.journal'].browse(journal_id)
        elif invoice['type'] == 'in_invoice':
            journal = self.env['account.journal'].search([('type', '=', 'purchase')], limit=1)
        else:
            journal = self.env['account.journal'].search([('type', '=', 'sale')], limit=1)
        values['journal_id'] = journal.id

        values['type'] = TYPE2REFUND[invoice['type']]
        values['date_invoice'] = date_invoice or fields.Date.context_today(invoice)
        if values.get('date_due', False) and values['date_invoice']:
            # To ensure that the date_invoice is a date object
            if self._fields['date_invoice'].to_date(values['date_invoice']) > values['date_due']:
                values['date_due'] = values['date_invoice']
        values['state'] = 'draft'
        values['number'] = False
        values['origin'] = invoice.number
        values['payment_term_id'] = invoice.payment_term_id.id #SC modif gesprim
        values['refund_invoice_id'] = invoice.id

        if values['type'] == 'in_refund':
            partner_bank_result = self._get_partner_bank_id(values['company_id'])
            if partner_bank_result:
                values['partner_bank_id'] = partner_bank_result.id

        if date:
            values['date'] = date
        if description:
            values['name'] = description
        return values
    
    @api.multi
    @api.depends("origin")
    def _compute_date_piece_orig(self):
        for invoice in self:
            if invoice.type == 'out_refund':
                piece_orig = self.env['account.invoice'].search([('number','=',invoice.origin)],limit=1)
                if piece_orig:
                    invoice.di_date_piece_orig = piece_orig.date_invoice
    
    @api.multi
    @api.depends("invoice_line_ids")
    def _compute_nb_lignes(self):
        for invoice in self:
            invoice.di_nb_lig = len(invoice.invoice_line_ids)
    
    @api.model
    def create(self,vals):        
        res = super(AccountInvoice, self).create(vals)        
        for invoice in res:   
            if invoice.di_nbex==0: 
                if invoice.partner_id:                
                    invoice.write({'di_nbex': invoice.partner_id.di_nbex_fac})                
        return res
    
    
    @api.onchange("partner_id")
    def di_onchange_partner(self):    
        if self.partner_id:
            self.di_nbex = self.partner_id.di_nbex_fac
            if self.partner_id.customer:
                if self.partner_id.di_period_fact != 'DEMANDE':
                    if self.partner_id.di_period_fact == 'DECADE':
                        message = {
                                    'title': ('Attention'),
                                    'message' : "Ce client est à la décade, il n’est pas conseillé de faire une facture directe."
                                }
                    if self.partner_id.di_period_fact == 'SEMAINE':
                        message = {
                                    'title': ('Attention'),
                                    'message' : "Ce client est à la semaine, il n’est pas conseillé de faire une facture directe."
                                }
                    if self.partner_id.di_period_fact == 'QUINZAINE':
                        message = {
                                    'title': ('Attention'),
                                    'message' : "Ce client est à la quinzaine, il n’est pas conseillé de faire une facture directe."
                                }
                    if self.partner_id.di_period_fact == 'MOIS':
                        message = {
                                    'title': ('Attention'),
                                    'message' : "Ce client est au mois, il n’est pas conseillé de faire une facture directe."
                                }
                        
                                        
                    return {'warning': message}
                    
    
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
        round_curr = self.currency_id.round
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
                    tax_grouped[key]['base'] = round_curr(val['base'])
                else:
                    tax_grouped[key]['amount'] += val['amount']
                    tax_grouped[key]['base'] += round_curr(val['base'])
        return tax_grouped
    
    
    def _prepare_invoice_line_from_po_line(self, line):
        # copie standard
        #Copie du standard pour ajouter des éléments dans data
        if line.product_id.purchase_method == 'purchase':
            qty = line.product_qty - line.qty_invoiced
            di_qte_un_saisie = line.di_qte_un_saisie - line.di_qte_un_saisie_fac
            di_poib = line.di_poib - line.di_poib_fac 
            di_poin = line.di_poin - line.di_poin_fac  
            di_nbpieces = line.di_nb_pieces - line.di_nb_pieces_fac
            di_nbcolis = line.di_nb_colis - line.di_nb_colis_fac
            di_nbpal = line.di_nb_palette - line.di_nb_palette_fac               
        #ajout difodoo
        else:
            qty = line.qty_received - line.qty_invoiced
            di_qte_un_saisie = line.di_qte_un_saisie_liv - line.di_qte_un_saisie_fac
            di_poib = line.di_poib_liv - line.di_poib_fac
            di_poin = line.di_poin_liv - line.di_poin_fac
            di_nbpieces = line.di_nb_pieces_liv - line.di_nb_pieces_fac
            di_nbcolis = line.di_nb_colis_liv - line.di_nb_colis_fac
            di_nbpal = line.di_nb_palette_liv - line.di_nb_palette_fac
            
        di_tare = di_poib - di_poin
        if di_nbcolis != 0.0:
            di_tare_un = di_tare / ceil(di_nbcolis)
        else:
            di_tare_un = 0.0
        #ajout difodoo
        if float_compare(qty, 0.0, precision_rounding=line.product_uom.rounding) <= 0:
            qty = 0.0
        taxes = line.taxes_id
        invoice_line_tax_ids = line.order_id.fiscal_position_id.map_tax(taxes, line.product_id, line.order_id.partner_id)
        invoice_line = self.env['account.invoice.line']
        date = self.date or self.date_invoice
        data = {
            'purchase_line_id': line.id,
            'name': line.order_id.name+': '+line.name,
            'origin': line.order_id.origin,
            'uom_id': line.product_uom.id,
            'product_id': line.product_id.id,
            'account_id': invoice_line.with_context({'journal_id': self.journal_id.id, 'type': 'in_invoice'})._default_account(),
            'price_unit': line.order_id.currency_id._convert(
                line.price_unit, self.currency_id, line.company_id, date or fields.Date.today(), round=False),
            'quantity': qty,
            'discount': 0.0,
            'account_analytic_id': line.account_analytic_id.id,
            'analytic_tag_ids': line.analytic_tag_ids.ids,
            'invoice_line_tax_ids': invoice_line_tax_ids.ids,
            #Ajout des éléments difodoo
            'di_tare_un':di_tare_un,
            'di_tare':di_tare,   
            'di_un_saisie':line.di_un_saisie,
            'di_type_palette_id':line.di_type_palette_id,
            'di_product_packaging_id':line.product_packaging,
            'di_un_prix':line.di_un_prix,
            'di_qte_un_saisie':di_qte_un_saisie,
            'di_poib':di_poib,
            'di_poin':di_poin,
            'di_nb_pieces':di_nbpieces,
            'di_nb_colis':di_nbcolis,
            'di_nb_palette':di_nbpal                                
        }
        account = invoice_line.get_invoice_line_account('in_invoice', line.product_id, line.order_id.fiscal_position_id, self.env.user.company_id)
        if account:
            data['account_id'] = account.id
        return data
    
    @api.one
    @api.depends('invoice_line_ids.price_subtotal', 'tax_line_ids.amount', 'tax_line_ids.amount_rounding',
                 'currency_id', 'company_id', 'date_invoice', 'type')
    def _compute_amount(self):      # on surcharge pour avoir des totaux signés pour chaque colonne + corriger le fait que le total ht soit en devise dossier (devise facture pour les autres)
        super(AccountInvoice, self)._compute_amount()
        round_curr = self.currency_id.round
        di_amount_tax_signed = sum(round_curr(line.amount_total) for line in self.tax_line_ids)
        di_amount_untaxed_signed = self.amount_untaxed
        sign = self.type in ['in_refund', 'out_refund'] and -1 or 1
        self.di_amount_tax_signed = di_amount_tax_signed * sign
        self.di_amount_untaxed_signed = di_amount_untaxed_signed * sign
     
class AccountInvoiceLine(models.Model):
    _inherit = "account.invoice.line"
    
    modifparprg = False
     
    di_qte_un_saisie = fields.Float(string='Quantité en unité de saisie') #, store=True)
    di_un_saisie = fields.Selection([("PIECE", "Pièce"), ("COLIS", "Colis"), ("PALETTE", "Palette"), ("KG", "Kg")], string="Unité de saisie", store=True)
    di_type_palette_id = fields.Many2one('product.packaging', string='Palette', store=True) 
    di_nb_pieces = fields.Integer(string='Nb pièces')   # compute="_compute_qte_aff", store=True
    di_nb_colis = fields.Float(string='Nb colis', digits=(8,1))   # compute="_compute_qte_aff"
    di_nb_palette = fields.Float(string='Nb palettes')   # compute="_compute_qte_aff"
    di_poin = fields.Float(string='Poids net')  # , store=True
    di_poib = fields.Float(string='Poids brut') # , store=True
    di_tare = fields.Float(string='Tare') # , store=True,compute="_compute_tare")
    di_product_packaging_id = fields.Many2one('product.packaging', string='Package', default=False, store=True)
    di_un_prix      = fields.Selection([("PIECE", "Pièce"), ("COLIS", "Colis"),("PALETTE", "Palette"),("KG","Kg")], string="Unité de prix",store=True)
    di_flg_modif_uom = fields.Boolean(default=False)
    di_tare_un = fields.Float(string='Tare unitaire')
    
    di_spe_saisissable = fields.Boolean(string='Champs spé saisissables',default=False,compute='_di_compute_spe_saisissable',store=True)
    
    def di_get_blno(self):
        blno=''
        if self.ensure_one():
            for sol in self.sale_line_ids:
                for sm in sol.move_ids:
                    if sm.picking_id:
                        if sm.picking_id.name:
                            blno = sm.picking_id.name
                            break                            
        return blno
             
        
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
            nbcol = round(self.di_nb_colis,1)
#             di_qte_prix = self.di_nb_colis
            di_qte_prix = nbcol
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
                line.price_unit = self.di_recherche_prix_unitaire(line.price_unit,line.invoice_id.partner_id,line.product_id,line.di_un_prix,di_qte_prix,line.invoice_id.date,line.di_product_packaging_id,line.di_type_palette_id)            
     
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
                self.di_product_packaging_id = ref.di_type_colis_id    
                self.di_un_prix = ref.di_un_prix    
                self.di_spe_saisissable = self.product_id.di_spe_saisissable                  
            else:
                if self.product_id:
                    self.di_un_saisie = self.product_id.di_un_saisie
                    self.di_type_palette_id = self.product_id.di_type_palette_id
                    self.di_product_packaging_id = self.product_id.di_type_colis_id    
                    self.di_un_prix = self.product_id.di_un_prix    
                    self.di_spe_saisissable = self.product_id.di_spe_saisissable                                    
                
                
    @api.multi 
    @api.onchange('di_poib')
    def _di_onchange_poib(self):
        if self.ensure_one():
            if self.di_un_saisie == 'KG':
                self.di_qte_un_saisie = self.di_poib
            else:
                self.di_poin = self.di_poib - self.di_tare
                if self.uom_id:
                    if self.uom_id.name.lower() == 'kg' and self.quantity != self.di_poin: # si la qté std n'est pas modifiée le flag modifparprg reste à vrai
                        AccountInvoiceLine.modifparprg=True
                        self.quantity = self.di_poin
                                
    @api.multi 
    @api.onchange('di_poin')
    def _di_onchange_poin(self):
        if self.ensure_one():
            self.di_tare = self.di_poib-self.di_poin      
#             self.di_poib = self.di_poin+self.di_tare       
#             if self.di_un_saisie == 'KG':
#                 self.di_qte_un_saisie = self.di_poib
#             else:       
            if self.di_un_saisie != 'KG':         
                if self.uom_id:
                    if self.uom_id.name.lower() == 'kg' and self.quantity != self.di_poin:# si la qté std n'est pas modifiée le flag modifparprg reste à vrai
                        AccountInvoiceLine.modifparprg=True
                        self.quantity = self.di_poin
    @api.multi 
    @api.onchange('di_tare')
    def _di_onchange_tare(self):
        if self.ensure_one():    
            self.di_poin = self.di_poib - self.di_tare        
            if self.di_un_saisie == 'KG':
                self.di_qte_un_saisie = self.di_poib
            else:
                if self.uom_id:
                    if self.uom_id.name.lower() == 'kg' and self.quantity != self.di_poin: # si la qté std n'est pas modifiée le flag modifparprg reste à vrai
                        AccountInvoiceLine.modifparprg=True
                        self.quantity = self.di_poin
              
                 
    @api.multi    
    @api.onchange('quantity')
    def _di_modif_qte_un_mesure(self):
        if self.ensure_one():
            if self.product_id:
                if AccountInvoiceLine.modifparprg == False:
                    if self.uom_id:
                        if self.uom_id.name.lower() == 'kg':
                            # si géré au kg, on ne modife que les champs poids
                            self.di_poin = self.quantity 
                            self.di_poib = self.di_poin + self.di_tare
                            
                        if self.uom_id.name == 'Unit(s)' or self.uom_id.name == 'Pièce' :
                            self.di_nb_pieces = ceil(self.quantity)
                        if self.uom_id.name.lower() ==  'colis' :
                            self.di_nb_colis = round(self.quantity,1)
                        if self.uom_id.name.lower() ==  'palette' :
                            self.di_nb_palette = ceil(self.quantity) 
                                                       
                        self.di_flg_modif_uom = True
                AccountInvoiceLine.modifparprg=False
            
    @api.multi    
    @api.onchange('di_nb_colis', 'di_tare_un','di_qte_un_saisie')
    def _di_recalcule_tare(self):
        if self.ensure_one():
            nbcol = round(self.di_nb_colis,1)
#             self.di_tare = self.di_tare_un * ceil(self.di_nb_colis)
            self.di_tare = self.di_tare_un * ceil(nbcol)
            
    @api.multi            
    @api.onchange('di_qte_un_saisie', 'di_un_saisie', 'di_type_palette_id', 'di_product_packaging_id')
    def _di_recalcule_quantites(self):
        if self.ensure_one():
            if self.product_id:
                quantity = self.quantity
                if self.di_flg_modif_uom == False:
                    self.di_tare_un = 0.0
                    self.di_tare = 0.0
#                     AccountInvoiceLine.modifparprg=True
                    if self.di_un_saisie == "PIECE":
                        self.di_nb_pieces = ceil(self.di_qte_un_saisie)
                        self.quantity = self.product_id.di_get_type_piece().qty * self.di_nb_pieces
                        if self.di_product_packaging_id.qty != 0.0 :
                            self.di_nb_colis = round(self.quantity / self.di_product_packaging_id.qty,1)
                        else:      
                            self.di_nb_colis = round(self.quantity,1) 
                        nbcol = round(self.di_nb_colis,1)            
                        if self.di_type_palette_id.di_qte_cond_inf != 0.0:
#                             self.di_nb_palette = self.di_nb_colis / self.di_type_palette_id.di_qte_cond_inf
                            self.di_nb_palette = nbcol / self.di_type_palette_id.di_qte_cond_inf
                        else:
#                             self.di_nb_palette = self.di_nb_colis
                            self.di_nb_palette = nbcol
                        self.di_poin = self.quantity * self.product_id.weight 
                        self.di_poib = self.di_poin + self.di_tare
                               
                    elif self.di_un_saisie == "COLIS":
                        self.di_nb_colis = round(self.di_qte_un_saisie,1)
                        nbcol = round(self.di_nb_colis,1)
#                         self.quantity = self.di_product_packaging_id.qty * self.di_nb_colis
#                         self.di_nb_pieces = ceil(self.di_product_packaging_id.di_qte_cond_inf * self.di_nb_colis)
                        self.quantity = self.di_product_packaging_id.qty * nbcol
                        self.di_nb_pieces = ceil(self.di_product_packaging_id.di_qte_cond_inf * nbcol)
                        if self.di_type_palette_id.di_qte_cond_inf != 0.0:                
#                             self.di_nb_palette = self.di_nb_colis / self.di_type_palette_id.di_qte_cond_inf
                            self.di_nb_palette = nbcol / self.di_type_palette_id.di_qte_cond_inf
                        else:
#                             self.di_nb_palette = self.di_nb_colis
                            self.di_nb_palette = nbcol
                        self.di_poin = self.quantity * self.product_id.weight 
                        self.di_poib = self.di_poin + self.di_tare
                                              
                    elif self.di_un_saisie == "PALETTE":            
                        self.di_nb_palette = self.di_qte_un_saisie
                        if self.di_type_palette_id.di_qte_cond_inf != 0.0:
                            self.di_nb_colis = round(self.di_nb_palette * self.di_type_palette_id.di_qte_cond_inf,1)
                        else:
                            self.di_nb_colis = round(self.di_nb_palette,1)
                        nbcol = round(self.di_nb_colis,1)
#                         self.di_nb_pieces = ceil(self.di_product_packaging_id.di_qte_cond_inf * self.di_nb_colis)
#                         self.quantity = self.di_product_packaging_id.qty * self.di_nb_colis
                        self.di_nb_pieces = ceil(self.di_product_packaging_id.di_qte_cond_inf * nbcol)
                        self.quantity = self.di_product_packaging_id.qty * nbcol
                        self.di_poin = self.quantity * self.product_id.weight 
                        self.di_poib = self.di_poin + self.di_tare
                         
                    elif self.di_un_saisie == "KG":                        
                        self.di_poib = self.di_qte_un_saisie
                        self.di_poin = self.di_poib - self.di_tare
                        if self.product_id.weight  != 0.0:
                            self.di_nb_pieces = ceil(self.di_poin / self.product_id.weight )
                        else:
                            self.di_nb_pieces = ceil(self.di_poin)                                            
                        if self.di_product_packaging_id.qty !=0.0:
                            self.di_nb_colis = round(self.di_nb_pieces / self.di_product_packaging_id.qty,1)
                        else:
                            self.di_nb_colis = round(self.di_nb_pieces,1)   
                        nbcol = round(self.di_nb_colis,1)                        
#                         self.quantity = self.di_product_packaging_id.qty * self.di_nb_colis
                        self.quantity = self.di_product_packaging_id.qty * nbcol                           
                        if self.di_type_palette_id.di_qte_cond_inf !=0.0:    
#                             self.di_nb_palette = self.di_nb_colis / self.di_type_palette_id.di_qte_cond_inf
                            self.di_nb_palette = nbcol / self.di_type_palette_id.di_qte_cond_inf
                        else:  
#                             self.di_nb_palette = self.di_nb_colis
                            self.di_nb_palette = nbcol
                         
                    else:
                        self.di_poib = self.di_qte_un_saisie
                        self.di_poin = self.di_poib - self.di_tare
                        if self.product_id.weight  != 0.0:
                            self.di_nb_pieces = ceil(self.di_poin / self.product_id.weight )
                        else:
                            self.di_nb_pieces = ceil(self.di_poin) 
                        if self.di_product_packaging_id.qty !=0.0:
                            self.di_nb_colis = round(self.di_nb_pieces / self.di_product_packaging_id.qty,1)
                        else:
                            self.di_nb_colis = round(self.di_nb_pieces,1)
                        nbcol = round(self.di_nb_colis,1)
#                         self.quantity = self.di_product_packaging_id.qty * self.di_nb_colis
                        self.quantity = self.di_product_packaging_id.qty * nbcol
                        if self.di_type_palette_id.di_qte_cond_inf !=0.0:    
#                             self.di_nb_palette = self.di_nb_colis / self.di_type_palette_id.di_qte_cond_inf
                            self.di_nb_palette = nbcol / self.di_type_palette_id.di_qte_cond_inf
                        else:  
#                             self.di_nb_palette = self.di_nb_colis
                            self.di_nb_palette = nbcol
                    if quantity != self.quantity:
                    # la quantité en unité de mesure à changer, on met le flag pour ne pas recalculé les qtés spé
                        AccountInvoiceLine.modifparprg = True  
             
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
            poin = 0.0
            nbpieces = 0
            nbcolis = 0
            nbpal = 0            
            for id_ligne in vals["sale_line_ids"][0][2]:
                Disaleorderline = self.env['sale.order.line'].search([('id', '=', id_ligne)], limit=1)                                 
                if Disaleorderline.id != False:               
                    #on attribue par défaut les valeurs de la ligne de commande   
#                     vals["di_tare"] = Disaleorderline.di_tare  
                    di_un_saisie = Disaleorderline.di_un_saisie
                    vals["di_un_saisie"] = Disaleorderline.di_un_saisie
                    vals["di_type_palette_id"] = Disaleorderline.di_type_palette_id.id
                    vals["di_product_packaging_id"] = Disaleorderline.product_packaging.id 
                    vals["di_un_prix"] = Disaleorderline.di_un_prix
                    vals["di_flg_modif_uom"]=Disaleorderline.di_flg_modif_uom
                    qte_a_fac += Disaleorderline.di_qte_a_facturer_un_saisie   
                    poib += Disaleorderline.di_poib_a_facturer
                    poin += Disaleorderline.di_poin_a_facturer
                    nbpieces += Disaleorderline.di_nb_pieces_a_facturer
                    nbcolis += Disaleorderline.di_nb_colis_a_facturer
                    nbpal += Disaleorderline.di_nb_palette_a_facturer
                                        
# temporaire herau
#             # on met à jour la colonne colonne quantité en unité de saisie pour qu'elle soit égale à la colonne correspondante
#             if di_un_saisie == "KG":
#                 qte_a_fac = poib
#             elif di_un_saisie == "PIECE":
#                 qte_a_fac = nbpieces
#             elif di_un_saisie == "COLIS":
#                 qte_a_fac = nbcolis
#             elif di_un_saisie == "PALETTE":
#                 qte_a_fac = nbpal                     
                     
            vals["di_qte_un_saisie"] = qte_a_fac
            vals["di_poib"] = poib
            vals["di_poin"] = poin      
            vals["di_tare"] = poib-poin
            if ceil(nbcolis) != 0.0:
                vals["di_tare_un"] = (poib-poin)  / ceil(nbcolis)
            vals["di_nb_pieces"] = nbpieces
            vals["di_nb_colis"] = nbcolis
            vals["di_nb_palette"] = nbpal      
            
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
#                     vals["di_tare"] = Dipurchaseorderline.di_tare  
                    vals["di_un_saisie"] = Dipurchaseorderline.di_un_saisie
                    vals["di_type_palette_id"] = Dipurchaseorderline.di_type_palette_id.id
                    vals["di_product_packaging_id"] = Dipurchaseorderline.product_packaging.id 
                    vals["di_un_prix"] = Dipurchaseorderline.di_un_prix
                    
                    qte_a_fac += Dipurchaseorderline.di_qte_a_facturer_un_saisie   
                    poib += Dipurchaseorderline.di_poib_a_facturer
                    poin += Dipurchaseorderline.di_poin_a_facturer
                    nbpieces += Dipurchaseorderline.di_nb_pieces_a_facturer
                    nbcolis += Dipurchaseorderline.di_nb_colis_a_facturer
                    nbpal += Dipurchaseorderline.di_nb_palette_a_facturer
                    
#                     qte_a_fac += Dipurchaseorderline.di_qte_un_saisie   
#                     poib += Dipurchaseorderline.di_poib
#                     poin += Dipurchaseorderline.di_poin
                     
            vals["di_qte_un_saisie"] = qte_a_fac
            vals["di_poib"] = poib
            vals["di_poin"] = poin
            vals["di_tare"] = poib-poin 
            if ceil(nbcolis) != 0.0:
                vals["di_tare_un"] = (poib-poin)  / ceil(nbcolis)
            vals["di_nb_pieces"] = nbpieces
            vals["di_nb_colis"] = nbcolis
            vals["di_nb_palette"] = nbpal 
  
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
#         round_tax =False
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