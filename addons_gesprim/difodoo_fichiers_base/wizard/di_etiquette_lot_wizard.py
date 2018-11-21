# -*- coding: utf-8 -*-
 
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
 
class DiEtiqLotWiz(models.TransientModel):
    _name = "di.etiqlot_wiz"
    _description = 'Impression étiquettes lot'
    
    product_id = fields.Many2one("product.template", string="Article", required=True)
    di_lot_txt = fields.Char(string="Lot", required=True, help="""Lot qui appaîtra sur l'étiquette""")
    weigth = fields.Float(string="Poids", required=True, help="""Poids qui appaîtra sur l'étiquette""")
    di_poin = fields.Float(string="Poids total", compute='_compute_poidstotal', store=True, readonly=True)
    di_nb_colis  = fields.Integer(string="Quantité", required=True, help="""Nombre d'étiquettes""",default=1.0)
    company_id = fields.Many2one('res.company', string='Société', readonly=True,  default=lambda self: self.env.user.company_id)
    order_id = fields.Many2one('sale.order', string='Order Reference') # pour ne pas déclencher d'erreur à l'édition  
    
    @api.multi
    @api.depends('weigth', 'di_nb_colis')
    def _compute_poidstotal(self):
        for etiq in self:
            if etiq.weigth and etiq.di_nb_colis:
                etiq.di_poin = etiq.weigth * etiq.di_nb_colis 

    @api.model
    def default_get(self, fields):
        res = super(DiEtiqLotWiz, self).default_get(fields)
        # récupération de l'article sélectionné
        if not self.env.context["active_id"]:
            raise ValidationError("Pas d'enregistrement selectionné")
        res["product_id"] = self.env.context["active_id"]
        Product = self.env["product.template"].browse(res["product_id"])
         
        if Product.di_type_colis_id:
            res["weigth"] = Product.weight*Product.di_type_colis_id.qty
        else:
            res["weigth"] = Product.weight
        # récupération des conditionnements par défaut       
        return res

    @api.multi
    def di_imp_etiqlot(self):                                                     
        return self.env.ref('difodoo_fichiers_base.di_wiz_report_etiqlot').report_action(self)
