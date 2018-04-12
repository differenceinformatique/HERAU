
# -*- coding: utf-8 -*-

from odoo import api, fields, models
from datetime import date, timedelta, datetime
from odoo.exceptions import ValidationError


class WizReferArticle(models.TransientModel):
    _name = "wiz.refer.article"
    _description = "Wizard de référencement d'articles à un client"
    
    partner_id = fields.Many2one("res.partner", string="Tiers associé", required=True)
    di_refarticle_ids = fields.Many2many("product.product")

    
#     product_id = fields.Many2one("product.product", string="Article associé", required=True)    
#     di_un_saisie        = fields.Selection([("PIECE", "Pièce"), ("COLIS", "Colis"),("PALETTE", "Palette"),("KG","Kg")], string="Unité de saisie")
#     di_type_palette_id     = fields.Many2one('product.packaging', string='Palette par défaut')   
#     di_type_colis_id       = fields.Many2one('product.packaging', string='Colis par défaut')
#     di_un_prix      = fields.Selection([("PIECE", "Pièce"), ("COLIS", "Colis"),("PALETTE", "Palette"),("KG","Kg")], string="Unité de prix")
    
    message = fields.Text(string="Information")
    
    @api.multi
    def referencer_article(self):
        # parcours des produits de la liste pour les enregistrer 
        for product_id in self.di_refarticle_ids:
            product_id.write({"di_reftiers_ids":[(4,self.partner_id.id,product_id.id)]})
            
        # recherche du res.partner    
        Partner = self.env["res.partner"].browse(self.partner_id).id
        # boucle pour supprimer les liens si on ne les a plus dans la liste
        for product in Partner.di_refarticle_ids:
            if product not in self.di_refarticle_ids:
                product.write({"di_reftiers_ids":[(3,self.partner_id.id,product_id.id)]})
                 
        self.message = "Rattachement des articles effectué."        
        return self.message
    
    @api.model
    def default_get(self, fields):
        res = super(WizReferArticle, self).default_get(fields)        
        res["partner_id"] = self.env.context["active_id"]
        # récupération du tiers sélectionné
        Partner = self.env["res.partner"].browse(res["partner_id"]) 
        
        #ProductPack = self.search([('name','=',self.name),('product_id', '=', self.product_id.id),('id','!=',self.id)], limit=1)
        #récupération de la liste d'article du tiers
        res["di_refarticle_ids"] = Partner.di_refarticle_ids.ids
        # on vérifie qu'on a bien un tiers sélectionné
        if not self.env.context["active_id"]:
            raise ValidationError("Pas d'enregistrement selectionné.")
        return res
            
        
# class WizListArt(models.TransientModel):
#     _name = "wiz.list.art"
#     _description = "Wizard contenant un article d'autres valeurs"
#     
#     product_id          = fields.Many2one("product.product", string="Article associé", required=True)
#     di_un_saisie        = fields.Selection([("PIECE", "Pièce"), ("COLIS", "Colis"),("PALETTE", "Palette"),("KG","Kg")], string="Unité de saisie")
#     di_type_palette_id  = fields.Many2one('product.packaging', string='Palette par défaut')   
#     di_type_colis_id    = fields.Many2one('product.packaging', string='Colis par défaut')
#     di_un_prix          = fields.Selection([("PIECE", "Pièce"), ("COLIS", "Colis"),("PALETTE", "Palette"),("KG","Kg")], string="Unité de prix")
