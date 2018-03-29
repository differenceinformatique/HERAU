# -*- coding: utf-8 -*-

from odoo import api, fields, models
from datetime import date, timedelta, datetime
from odoo.exceptions import ValidationError


class DiGenTarWiz(models.TransientModel):
    _name = "di.gen.tar.wiz"
    _description = "Wizard de génération de tarifs"
    
    di_tarif_orig_id = fields.Many2one("di.code.tarif", string="Code tarif origine", required=True)
    di_date_effet = fields.Datetime(string="Date d'effet", required=True)
    di_date_fin = fields.Datetime(string="Date de fin")
    di_tarifs_dest_ids = fields.Many2many("di.code.tarif")
    
    @api.multi
    def generer_tarifs(self):
        # parcours des codes tarifs  
        for tarifdest in self.di_tarifs_dest_ids:
            if tarifdest.id != self.di_tarif_orig_id.id:
                for tarif_origine in self.env["di.tarifs"].search([('di_code_tarif_id', '=', self.di_tarif_orig_id.id)]):
                    data = {
                            'di_product_id': tarif_origine.di_product_id.id,
                            'di_code_tarif_id': tarifdest.id,
                            'di_partner_id': tarif_origine.di_partner_id.id,
                            'di_un_prix': tarif_origine.di_un_prix,
                            'di_prix': tarif_origine.di_prix * tarifdest.di_coef,
                            'di_qte_seuil': tarif_origine.di_qte_seuil,
                            'di_date_effet': self.di_date_effet,
                            'di_date_fin': self.di_date_fin                                  
                            }   
                    self.env["di.tarifs"].create(data)
            
    @api.model
    def default_get(self, fields):
        res = super(DiGenTarWiz, self).default_get(fields)    
            
        tarif_id = self.env.context["active_id"]
        
        # récupération du tiers sélectionné
        Tarif = self.env["di.tarifs"].browse(tarif_id)
        res["di_tarif_orig_id"] = Tarif.di_code_tarif_id.id
        
        #ProductPack = self.search([('name','=',self.name),('product_id', '=', self.product_id.id),('id','!=',self.id)], limit=1)
        #récupération de la liste d'article du tiers
        res["di_date_effet"] = Tarif.di_date_effet
        res["di_date_fin"] = Tarif.di_date_fin
        # on vérifie qu'on a bien un tiers sélectionné
#         if not self.env.context["active_id"]:
#             raise ValidationError("Pas d'enregistrement selectionné.")
        return res    