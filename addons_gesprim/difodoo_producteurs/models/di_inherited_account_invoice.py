
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
   

    def _prepare_invoice_line_from_po_line(self, line): # revoir v12
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
            'di_tare':line.di_tare,  
            'di_un_saisie':line.di_un_saisie,
            'di_type_palette_id':line.di_type_palette_id,
            
            'di_categorie_id':line.di_categorie_id,
            'di_origine_id':line.di_origine_id,
            'di_marque_id':line.di_marque_id,
            'di_calibre_id':line.di_calibre_id,                       
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
    
   
    
    di_categorie_id = fields.Many2one("di.categorie",string="Catégorie")    
    di_categorie_di_des = fields.Char(related='di_categorie_id.di_des')#, store='False')
    
    di_origine_id = fields.Many2one("di.origine",string="Origine")
    di_origine_di_des = fields.Char(related='di_origine_id.di_des')#, store='False')
    
    di_marque_id = fields.Many2one("di.marque",string="Marque")
    di_marque_di_des = fields.Char(related='di_marque_id.di_des')#, store='False')
    
    di_calibre_id = fields.Many2one("di.calibre",string="Calibre")
    di_calibre_di_des = fields.Char(related='di_calibre_id.di_des')#, store='False')
    
    di_station_id = fields.Many2one("stock.location",string="Station")
    di_station_di_des = fields.Char(related='di_station_id.name')#, store='False')
    
    di_courtier_id = fields.Many2one("res.partner",string="Metteur en marche")
    di_prc_com_court = fields.Float(string='% com. Metteur en marche',help="""Pourcentage de commission que le metteur en marche récupère sur la vente. """, default=0.0,store=True)
    di_prc_com_OP = fields.Float(string='% com. OP',help="""Pourcentage de commission que l'OP récupère sur la vente. """,store=True)#,compute='_di_compute_com_op')
    
    @api.onchange('product_id')
    def _di_charger_prc_op(self):   
        if self.di_prc_com_OP == 0.0:
            param = self.env['di.param'].search([('di_company_id','=',self.env.user.company_id.id)])
            if self.di_courtier_id:
                if self.di_courtier_id.di_is_court:
                    self.di_prc_com_OP = param.di_prc_com_avec_court
                else:
                    self.di_prc_com_OP = param.di_prc_com_sans_court
            else:
                self.di_prc_com_OP = param.di_prc_com_sans_court
                
    @api.onchange('di_courtier_id')
    def _di_charger_prc_court(self):
        param = self.env['di.param'].search([('di_company_id','=',self.env.user.company_id.id)])
        if self.di_courtier_id:            
            if self.di_courtier_id.di_is_court:
                self.di_prc_com_OP = param.di_prc_com_avec_court
                self.di_prc_com_court = self.di_courtier_id.di_prc_com_avec_court
            else:
                self.di_prc_com_court = 0.0
                self.di_prc_com_OP = param.di_prc_com_sans_court
        else:
            self.di_prc_com_court = 0.0   
            self.di_prc_com_OP = param.di_prc_com_sans_court            
    
    @api.multi            
    @api.onchange('product_id')
    def _di_charger_valeur_par_defaut(self):
        super(AccountInvoiceLine, self)._di_charger_valeur_par_defaut()
        if self.ensure_one():
            if self.partner_id and self.product_id:
                ref = self.env['di.ref.art.tiers'].search([('di_partner_id','=',self.partner_id.id),('di_product_id','=',self.product_id.id)],limit=1)
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
                               
                    vals["di_categorie_id"]=Disaleorderline.di_categorie_id.id
                    vals["di_origine_id"]=Disaleorderline.di_origine_id.id
                    vals["di_marque_id"]=Disaleorderline.di_marque_id.id
                    vals["di_calibre_id"]=Disaleorderline.di_calibre_id.id
                    vals["di_station_id"]=Disaleorderline.di_station_id.id                    
                    vals["di_courtier_id"]=Disaleorderline.di_courtier_id.id
                    vals["di_prc_com_court"]=Disaleorderline.di_prc_com_court
                    vals["di_prc_com_OP"]=Disaleorderline.di_prc_com_OP                                                                             
            
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
                    vals["di_categorie_id"]=Dipurchaseorderline.di_categorie_id.id
                    vals["di_origine_id"]=Dipurchaseorderline.di_origine_id.id
                    vals["di_marque_id"]=Dipurchaseorderline.di_marque_id.id
                    vals["di_calibre_id"]=Dipurchaseorderline.di_calibre_id.id
                    vals["di_station_id"]=Dipurchaseorderline.di_station_id.id      
  
        res = super(AccountInvoiceLine, self).create(vals)                           
        return res
