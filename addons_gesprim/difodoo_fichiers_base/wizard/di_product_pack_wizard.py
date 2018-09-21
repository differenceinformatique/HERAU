# -*- coding: utf-8 -*-
 
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
 
class DiProdPackWiz(models.TransientModel):
    _name = "di.prodpack_wiz"
    _description = 'Generation Conditionnements'
    
    product_id = fields.Many2one("product.template", string="Article", required=True)
    cond_ids = fields.Many2many("di.conddefaut", string="Conditionnements")
    uom_id = fields.Many2one("product.uom", string="Unité de mesure", required=True)
    weight = fields.Float(string='Poids')
    QtePiece = fields.Float(string='Quantité en unité de mesure pour une pièce')
     
    @api.model
    def default_get(self, fields):
        res = super(DiProdPackWiz, self).default_get(fields)
        # récupération de l'article sélectionné
        if not self.env.context["active_id"]:
            raise ValidationError("Pas d'enregistrement selectionné")
        res["product_id"] = self.env.context["active_id"]
        Product = self.env["product.template"].browse(res["product_id"]) 
        res["uom_id"] = Product.uom_id.id
        res["weight"] = Product.weight
        # récupération des conditionnements par défaut
        res["cond_ids"] = self.env['di.conddefaut'].search([]).ids        
        return res

    @api.multi
    def di_gen_cond(self):
        # parcours des conditionnement de la liste pour les enregistrer 
        for Cond in self.cond_ids:
            product = self.env['product.product'].search([('product_tmpl_id', '=', self.product_id.id)], limit=1)
            Existe = self.env['product.packaging'].search(['&', ('product_id', '=', product.id), ('name', '=', Cond.name)])
            if not Existe:                
                if Cond.di_type_cond=='PIECE':
                    self.env['product.packaging'].create({'name' : Cond.name , 'product_id' : product.id, 'di_type_cond' : Cond.di_type_cond, 'di_qte_cond_inf' : 1, 'qty' : self.QtePiece})
                else:
                    self.env['product.packaging'].create({'name' : Cond.name , 'product_id' : product.id, 'di_type_cond' : Cond.di_type_cond, 'di_qte_cond_inf' : 1})
        res = self.message = "Génération terminée."        
        return res
