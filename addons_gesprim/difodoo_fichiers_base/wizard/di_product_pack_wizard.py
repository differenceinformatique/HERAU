# -*- coding: utf-8 -*-
 
from odoo import api, fields, models, _
 
class DiProdPackWiz(models.TransientModel):
    _name = "di.prodpack_wiz"
    _description = 'Generation Conditionnements'
    
    product_id = fields.Many2one("product.template", string="Article", required=True)
    cond_ids = fields.Many2many("di.conddefaut",string="Conditionnements")
     
    @api.model
    def default_get(self, fields):
        res = super(DiProdPackWiz, self).default_get(fields)
        # récupération de l'article sélectionné
        res["product_id"] = self.env.context["active_id"]
        # récupération des conditionnements par défaut
        res["cond_ids"] = self.env['di.conddefaut'].search([]).ids
        if not self.env.context["active_id"]:
            raise ValidationError("Pas d'enregistrement selectionné")
        return res
    
    @api.multi
    def di_gen_cond(self):
#         # parcours des produits de la liste pour les enregistrer 
#         for product_id in self.di_refarticle_ids:
#             product_id.write({"di_reftiers_ids":[(4,self.partner_id.id,product_id.id)]})
#             
#         # recherche du res.partner    
#         Partner = self.env["res.partner"].browse(self.partner_id).id
#         # boucle pour supprimer les liens si on ne les a plus dans la liste
#         for product in Partner.di_refarticle_ids:
#             if product not in self.di_refarticle_ids:
#                 product.write({"di_reftiers_ids":[(3,self.partner_id.id,product_id.id)]})
#                  
#         self.message = "Rattachement des articles effectué."        
        return {}
