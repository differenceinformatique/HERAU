# -*- coding: utf-8 -*-
from odoo import osv
from odoo.exceptions import Warning
from odoo import models, fields, api
from xlrd.formula import FMLA_TYPE_COND_FMT

class DiInheritedProduct(models.Model):
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
    
    di_enlevement_id = fields.Many2one("di.enlevement",string="Enlèvement")
    di_enlevement_di_des = fields.Char(related='di_enlevement_id.di_des')#, store='False')
    
    di_producteur_id = fields.Many2one("res.partner",string="Producteur")
    di_producteur_nom = fields.Char(related='di_producteur_id.display_name')#, store='False')  
    
    di_un_saisie        = fields.Selection([("PIECE", "Pièce"), ("COLIS", "Colis"),("PALETTE", "Palette"),("POIDS","Poids")], string="Unité de saisie")
    di_type_palette     = fields.Many2one('product.packaging', string='Palette')   
    di_type_colis       = fields.Many2one('product.packaging', string='Colis')
     
    @api.one
    def di_get_type_piece(self):
        ProductPack = self.env['product.packaging'].search([
            '|',
            ('product_id', '=', self.id),
            ('di_type_cond', '=', 'PIECE')]).id
        return ProductPack
        
class DiInheritedProductProduct(models.Model):
    _inherit = "product.product"
    
    @api.multi
    def di_get_type_piece(self):
        ProductPack = self.env['product.packaging'].search(['&',('product_id', '=', self.id),('di_type_cond', '=', 'PIECE')])
        return ProductPack
        
class DiInheritedProductPackaging(models.Model):
    _inherit = "product.packaging"
    
    di_qte_cond_inf = fields.Float(string='Quantité conditionnement inférieur')
    di_type_cond    = fields.Selection([("PIECE", "Pièce"), ("COLIS", "Colis"),("PALETTE", "Palette")], string="Type de conditionnement")    
    di_type_colis       = fields.Many2one('product.packaging', string='Colis') 
           
    @api.model
    def create(self,vals):
        #surcharge de la fonction create
        if vals["di_type_cond"]=="PIECE": # si le type de conditionnement est PIECE
            #recherche de l'enregistrement product.packaging avec un type de conditionnement = PIECE
            ProductPack = self.env['product.packaging'].search(['&',('product_id', '=', vals["product_id"]),('di_type_cond', '=', vals["di_type_cond"])])
            #Si on ne le trouve pas: OK , on créé le packaging
            if ProductPack.id == False: 
                rec = super(DiInheritedProductPackaging, self).create(vals)            
            else:
                #sinon on retourne false -> pas de création avec un message d'erreur
                rec = False
                raise Warning("Vous ne pouvez pas avoir plusieurs conditionnements de type Pièce pour un même article.")   
        else:
             rec = super(DiInheritedProductPackaging, self).create(vals)
        return rec
    
    @api.multi
    def write(self,vals):   
        #surcharge de write
        modif_type_cond = False     # initialisation d'une variable       
        di_ctx=dict(self._context or {}) # chargement du contexte
        for key in vals.items(): # vals est un dictionnaire qui contient les champs modifiés, on va lire les différents enregistrements
            #on est obligé de faire cette boucle car quand on valide la fiche article, pour les conditionnements non modifiés on passe quand même ici avec
            # seulement la key product_id donc on au une erreur sur la suite car il ne trouve pas de vals["di_type_cond"]
            if key[0] == "di_type_cond": # si on a modifié di_type_cond
                modif_type_cond = True
        if modif_type_cond==True:
            if vals["di_type_cond"]=="PIECE": # si on a bien un type PIECE
                #recherche de l'enregistrement product.packaging avec un type de conditionnement = PIECE
                ProductPack = self.env['product.packaging'].search(['&',('product_id', '=', self.product_id.id),('di_type_cond', '=', vals["di_type_cond"])])            
                if ProductPack.id == False: 
                    #Si on ne le trouve pas: OK , on créé le packaging
                    rec = super(DiInheritedProductPackaging, self.with_context(di_ctx)).write(vals)            
                else:
                    rec = False
                    #sinon on retourne false -> pas de création avec un message d'erreur
                    raise Warning("Vous ne pouvez pas avoir plusieurs conditionnements de type Pièce pour un même article.")   
            else:
                 rec = super(DiInheritedProductPackaging, self.with_context(di_ctx)).write(vals)            
        else:
            rec = super(DiInheritedProductPackaging, self.with_context(di_ctx)).write(vals)
        return rec    
    