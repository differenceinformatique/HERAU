# -*- coding: utf-8 -*-

from odoo import osv
from odoo.exceptions import Warning
from odoo import models, fields, api
from xlrd.formula import FMLA_TYPE_COND_FMT
from suds import null
from odoo.tools.float_utils import float_round

class ProductTemplate(models.Model):
    _inherit = "product.template"
      
    di_lavage = fields.Boolean(string="Lavage", default=False)
    di_prixmin = fields.Float(string="Prix minimum")
    di_prixmax = fields.Float(string="Prix maximum")
    di_des = fields.Char(string="Désignation")
    
    di_categorie_id = fields.Many2one("di.categorie",string="Catégorie")    
    di_categorie_di_des = fields.Char(related='di_categorie_id.di_des')#, store='False')
    
    di_origine_id = fields.Many2one("di.origine",string="Origine")
    di_origine_di_des = fields.Char(related='di_origine_id.di_des')#, store='False')
    
    di_marque_id = fields.Many2one("di.marque",string="Marque")
    di_marque_di_des = fields.Char(related='di_marque_id.di_des')#, store='False')
    
    di_calibre_id = fields.Many2one("di.calibre",string="Calibre")
    di_calibre_di_des = fields.Char(related='di_calibre_id.di_des')#, store='False')
    
    di_station_id = fields.Many2one("di.station",string="Station")
    di_station_di_des = fields.Char(related='di_station_id.di_des')#, store='False')
    
    di_producteur_id = fields.Many2one("res.partner",string="Producteur")
    di_producteur_nom = fields.Char(related='di_producteur_id.display_name')#, store='False')  

    di_un_saisie        = fields.Selection([("PIECE", "Pièce"), ("COLIS", "Colis"),("PALETTE", "Palette"),("KG","Kg")], string="Type unité saisie")
    di_type_palette_id     = fields.Many2one('product.packaging', string='Palette par défaut')   
    di_type_colis_id       = fields.Many2one('product.packaging', string='Colis par défaut')
    di_un_prix      = fields.Selection([("PIECE", "Pièce"), ("COLIS", "Colis"),("PALETTE", "Palette"),("KG","Kg")], string="Type unité prix")
    
    @api.multi
    def write(self, vals):                              
        for key in vals.items():  # vals est un dictionnaire qui contient les champs modifiés, on va lire les différents enregistrements                      
            if key[0] == "di_un_prix":  # si on a modifié sale_line_id
                if vals['di_un_prix'] == False:
                    vals['di_un_saisie']=False
                    break
            elif key[0] == "di_un_saisie":
                if vals['di_un_saisie'] == False:
                    vals['di_un_prix']=False 
                    break                                    
        res = super(ProductTemplate, self).write(vals)
        return res   
           
    
class ProductProduct(models.Model):
    _inherit = "product.product"
    default_code = fields.Char('Internal Reference', index=True, copy=False)
        
    di_reftiers_ids = fields.Many2many('res.partner', 'di_referencement_article_tiers', 'product_id','partner_id', string='Référencement article')
    di_tarifs_ids = fields.One2many('di.tarifs', 'id',string='Tarifs de l\'article')
    
    def di_get_type_piece(self):
        ProductPack = self.env['product.packaging'].search(['&',('product_id', '=', self.id),('di_type_cond', '=', 'PIECE')])
        return ProductPack
    
    #unicité du code article
    @api.one
    @api.constrains('default_code')
    def _check_default_code(self):
        if self.default_code:
            default_code = self.search([
                ('id', '!=', self.id),
                ('default_code', '=', self.default_code)], limit=1)
            if default_code:
                raise Warning("Le code existe déjà.")
                     
    @api.multi
    def write(self, vals):     
                         
        # à l'écriture de l'article on va recalculer les quantités entre conditionnements
        # on commence par parcourir les emballages de type pièces, puis colis, puis palette
        for ProductPack in self.packaging_ids:
            if ProductPack.di_type_cond == 'PIECE':
                ProductPack.di_type_cond_inf_id = ''
                ProductPack.di_qte_cond_inf = 1
        for ProductPack in self.packaging_ids:
            if ProductPack.di_type_cond == 'COLIS':
                PP_Piece = self.env['product.packaging'].search(['&', ('product_id', '=', self.id), ('di_type_cond', '=', 'PIECE')], limit=1)
                if PP_Piece:
                    ProductPack.di_type_cond_inf_id = PP_Piece.id
                    ProductPack.qty = PP_Piece.qty*ProductPack.di_qte_cond_inf 
        for ProductPack in self.packaging_ids:
            if ProductPack.di_type_cond == 'PALETTE':
                PP_Colis = self.env['product.packaging'].browse(ProductPack.di_type_cond_inf_id).id
                if PP_Colis:
                    ProductPack.qty = PP_Colis.qty*ProductPack.di_qte_cond_inf 
        res = super(ProductProduct, self).write(vals)
        return res
    
#     @api.model
#     def create(self, vals):               
#         if not vals.get('default_code'):
#             vals['default_code']=self.env.ref('difodoo_fichiers_base.di_action_di_saisie_code_wiz').read([])[0]
#                       
#                              
#         if vals.get('default_code') and vals['default_code']!=False:
#             res = super(ProductProduct, self).create(vals)
#         else:
#             res =False
#         return res
    

class ProductPackaging(models.Model):
    _inherit = "product.packaging"
    
    di_qte_cond_inf = fields.Float(string='Quantité conditionnement inférieur')
    di_type_cond    = fields.Selection([("PIECE", "Pièce"), ("COLIS", "Colis"),("PALETTE", "Palette")], string="Type de conditionnement")    
    di_type_cond_inf_id   = fields.Many2one('product.packaging', string='Conditionnement inférieur')
    di_des          = fields.Char(string="Désignation")#, required=True)
    
    @api.onchange('di_type_cond', 'di_type_cond_inf_id', 'di_qte_cond_inf')
    def onchange_recalc_colisage(self):    #TODO à faire à l'écriture car les enregs ne sont pas à jour tant que l'article n'est pas sauvegardé
        if self.di_type_cond=='PIECE':
            self.di_type_cond_inf_id=''
            self.di_qte_cond_inf=1
        if self.di_type_cond=='COLIS':
            self.di_type_cond_inf_id=self.env['product.packaging'].search(['&',('product_id', '=', self.product_id.id),('di_type_cond', '=', 'PIECE')]).id
            self.qty = self.env['product.packaging'].search(['&',('product_id', '=', self.product_id.id),('di_type_cond', '=', 'PIECE')]).qty*self.di_qte_cond_inf
                   
    
    #vérifie qu'on a un seul conditionnement pièce par article
    @api.one
    @api.constrains('product_id','di_type_cond')
    def _check_cond_piece_article(self):
        if self.di_type_cond=="PIECE":
            ProductPack = self.search([('name','!=',self.name),('product_id', '=', self.product_id.id),('di_type_cond', '=', "PIECE")], limit=1)        
            if ProductPack:
                raise Warning("Vous ne pouvez pas avoir plusieurs conditionnements de type Pièce pour un même article.") 

    #vérifie l'unicité du nom du conditionnement pour un article
    @api.one
    @api.constrains('name')
    def _check_nom_unique_article(self):
        ProductPack = self.search([('name','=',self.name),('product_id', '=', self.product_id.id),('id','!=',self.id)], limit=1)        
        if ProductPack:
            raise Warning("Vous ne pouvez pas avoir plusieurs conditionnements avec le même nom pour un même article.") 
        


