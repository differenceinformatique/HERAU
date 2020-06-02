# -*- coding: utf-8 -*-
 
from odoo import api, fields, models, _
    
class DiResserre(models.Model):
    _name = "di.resserre"
    _description = "Resserre"
    _order = "name"
    
    di_company_id = fields.Many2one('res.company', string='Société', readonly=True,  default=lambda self: self.env.user.company_id)                 
    name = fields.Char(string="Name", compute='_compute_name', store=True)
    product_id = fields.Many2one('product.product', 'Article')
    uom_id = fields.Many2one('uom.uom', 'Unité de mesure')
    uom_name = fields.Char(string='Unité de mesure', related='uom_id.name')
    art_default_code = fields.Char(string='Code article', related='product_id.default_code')
    art_name = fields.Char(string='Désignation article', related='product_id.display_name')
    date = fields.Datetime('Date')
    di_prix_vente_moyen = fields.Float(string='Prix de vente moyen')
    di_prix_achat_moyen = fields.Float(string="Prix d'achat moyen")
    
    di_val_ven = fields.Float(string='Valeur vente')
    di_val_stock = fields.Float(string='Valeur stock')
    di_val_marge = fields.Float(string='Valeur marge')
    di_marge_prc = fields.Float(string='Marge %')
    
    di_col_stock = fields.Float(string='Colis en stock')
    di_qte_stock = fields.Float(string='Quantité en stock')

    di_poib_stock = fields.Float(string='Poids brut en stock')
    di_poin_stock = fields.Float(string='Poids net en stock')
    
    di_col_ven = fields.Float(string='Colis vendus')
    di_qte_ven = fields.Float(string='Quantité vendue')
    di_poib_ven = fields.Float(string='Poids brut vendu')
    di_poin_ven = fields.Float(string='Poids net vendu')  
    
    di_col_ach = fields.Float(string='Colis achetés')
    di_qte_ach = fields.Float(string='Quantité achetée')
    di_poib_ach = fields.Float(string='Poids brut acheté')
    di_poin_ach = fields.Float(string='Poids net acheté')  
    
    di_col_regul_entree = fields.Float(string='Colis régul.entrée')
    di_qte_regul_entree = fields.Float(string='Quantité régul. entrée')
    di_poib_reg_ent = fields.Float(string='Poids brut régul. entrée')
    di_poin_reg_ent = fields.Float(string='Poids net régul. entrée')
    
      
    di_col_regul_sortie = fields.Float(string='Colis régul. sortie')
    di_qte_regul_sortie = fields.Float(string='Quantité régul. sortie')
    di_poib_reg_sort = fields.Float(string='Poids brut régul. sortie')
    di_poin_reg_sort = fields.Float(string='Poids net régul. sortie')
    di_val_regul_sortie = fields.Float(string='Valeur régul. sortie')
    di_val_marge_ap_regul_sortie = fields.Float(string='Valeur marge après régul. sortie')
    
    di_date_date = fields.Date('Date sans heure', compute='_di_compute_date_date', store=True)
    di_date_date_str     = fields.Char(string="Date string",compute="_compute_date_string",copy=False,store=True)
    
    @api.depends("di_date_date")
    def _compute_date_string(self):
        for ress in self:
            if ress.di_date_date:
                ress.di_date_date_str = ress.di_date_date.strftime('%d/%m/%Y')
    
    @api.multi
    @api.depends('date')
    def _di_compute_date_date(self):        
        for ress in self:   
            if ress.date:
                ress.di_date_date = ress.date.date() 
    
    
    @api.multi
    @api.depends('product_id', 'date')
    def _compute_name(self):
        for ress in self:
            if ress.date and ress.product_id:
                ress.name = ress.product_id.display_name + ' ' + ress.date.strftime('%d/%m/%Y %H:%M:%S')