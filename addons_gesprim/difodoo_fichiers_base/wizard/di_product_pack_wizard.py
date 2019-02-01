# -*- coding: utf-8 -*-
 
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
 
class DiProdPackWiz(models.TransientModel):
    _name = "di.prodpack_wiz"
    _description = 'Generation Conditionnements'
    
    product_ids = fields.Many2many("product.template", string="Article")
    cond_ids = fields.Many2many("di.conddefaut", string="Conditionnements")        
    QtePiece = fields.Float(string='Quantité en unité de mesure pour une pièce')
     
    @api.model
    def default_get(self, fields):
        res = super(DiProdPackWiz, self).default_get(fields)
        # récupération de l'article sélectionné
        
        
        if self.env.context.get('active_model'): # on vérifie si on est dans un model
            active_model=self.env.context['active_model'] #récup du model courant
        else:
            active_model=''
        if active_model :    
            product_ids = self.env.context["active_ids"]
        else:
            product_ids =self.env['product.template'].search([]).ids                                    
#         product_id = self.env.context["active_id"]                            
            #raise ValidationError("Pas d'enregistrement selectionné")
#         res["product_id"] = product_id
        res["product_ids"] = product_ids
#         Product = self.env["product.template"].browse(res["product_id"])         
#         res["weight"] = Product.weight
        res["QtePiece"] = 1.0
        # récupération des conditionnements par défaut
        res["cond_ids"] = self.env['di.conddefaut'].search([]).ids        
        return res

    @api.multi
    def di_gen_cond(self):
        # parcours des conditionnement de la liste pour les enregistrer
        products = self.env['product.product'].search([('product_tmpl_id', 'in', self.product_ids.ids)])
        for product in products: 
            for Cond in self.cond_ids:            
                Existe = self.env['product.packaging'].search(['&', ('product_id', '=', product.id), ('name', '=', Cond.name)])
                if not Existe:                
                    if Cond.di_type_cond=='PIECE':
                        self.env['product.packaging'].create({'name' : Cond.name,'di_des':Cond.di_des, 'product_id' : product.id, 'di_type_cond' : Cond.di_type_cond, 'di_qte_cond_inf' : 1, 'qty' : self.QtePiece})
                    else:
                        self.env['product.packaging'].create({'name' : Cond.name,'di_des':Cond.di_des , 'product_id' : product.id, 'di_type_cond' : Cond.di_type_cond, 'di_qte_cond_inf' : 1})
        res = self.message = "Génération terminée."        
        return res
