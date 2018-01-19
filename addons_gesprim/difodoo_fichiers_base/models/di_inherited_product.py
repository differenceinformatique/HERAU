# -*- coding: utf-8 -*-
from odoo import models, fields, api
from xlrd.formula import FMLA_TYPE_COND_FMT

class DiInheritedProduct(models.Model):
    _inherit = "product.template"
    
    
    #di_default_code_req = fields.Char('Code article', store=False)
#     
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
    
#     di_emballage_id = fields.Many2one("di.emballage",string="Emballage")
#     di_emballage_di_des = fields.Char(related='di_emballage_id.di_des')#, store='False')
    
    di_enlevement_id = fields.Many2one("di.enlevement",string="Enlèvement")
    di_enlevement_di_des = fields.Char(related='di_enlevement_id.di_des')#, store='False')
    
    di_producteur_id = fields.Many2one("res.partner",string="Producteur")
    di_producteur_nom = fields.Char(related='di_producteur_id.display_name')#, store='False')  
    
    di_un_saisie        = fields.Selection([("PIECE", "Pièce"), ("COLIS", "Colis"),("PALETTE", "Palette"),("POIDS","Poids")], string="Unité de saisie")
    di_type_palette     = fields.Many2one('product.packaging', string='Palette')   
    di_type_colis       = fields.Many2one('product.packaging', string='Colis')
     
    @api.one
#     @api.model
    def di_get_type_piece(self):
#         if not self.id:
#             return False
#         ProductPackObj = self.env['product.packaging']
#         
#         return ProductPackObj.di_get_product_packaging(self.id,"PIECE")
        ProductPack = self.env['product.packaging'].search([
            '|',
            ('product_id', '=', self.id),
            ('di_type_cond', '=', 'PIECE')]).id
        return ProductPack
        

#     @api.model
#     def _auto_init(self):
#         #self.di_default_code_req.required=False        
#         super(DiInheritedProduct, self)._auto_init()
#         # Now safely perform your own stuff
#         self.env.cr.execute("update product_template set di_default_code_req = '3' where di_default_code_req is null;")
#         self.di_default_code_req.required=True
#        # super(DiInheritedProduct, self)._auto_init()
#         
#     @api.depends('di_default_code_req')
#     def _compute_default_code(self):
#       self.default_code = self.di_default_code_req

class DiInheritedProductProduct(models.Model):
    _inherit = "product.product"
    
    
    @api.multi
#     @api.model
    def di_get_type_piece(self):
#         if not self.id:
#             return False
#         ProductPackObj = self.env['product.packaging']
#         
#         return ProductPackObj.di_get_product_packaging(self.id,"PIECE")
        ProductPack = self.env['product.packaging'].search(['&',('product_id', '=', self.id),('di_type_cond', '=', 'PIECE')])
        return ProductPack
        


class DiInheritedProductPackaging(models.Model):
    _inherit = "product.packaging"
    
    di_qte_cond_inf = fields.Float(string='Quantité conditionnement inférieur')
    di_type_cond    = fields.Selection([("PIECE", "Pièce"), ("COLIS", "Colis"),("PALETTE", "Palette")], string="Type de conditionnement")
    # TODO : n'autoriser qu'un seul type pièce
    di_type_colis       = fields.Many2one('product.packaging', string='Colis') 
           
    @api.model
    def create(self, vals):
        if vals["di_type_cond"]=="PIECE":
            ProductPack = self.env['product.packaging'].search(['&',('product_id', '=', vals["product_id"]),('di_type_cond', '=', vals["di_type_cond"])])
            if ProductPack.id == False: 
                rec = super(ProductPackaging, self).create(vals)            
            else:
                rec = False
        else:
            rec = super(ProductPackaging, self).create(vals)
        return rec
    
#     @api.onchange('di_type_cond')
#     def di_controle_type_piece_unique(self):
#         if self.di_type_cond =='PIECE':
#             ProductPack = self.env['product.packaging'].search(['&',('product_id', '=', self.product_id),('di_type_cond', '=', self.di_type_cond)])
#             if ProductPack.id != False:             
#                 raise osv.except_osv(('Erreur'), ('Vous ne pouvez pas avoir plusieurs conditionement de type pièce.'))
#                 self.di_type_cond = 'COLIS'
    