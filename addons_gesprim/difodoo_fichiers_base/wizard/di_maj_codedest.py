# -*- coding: utf-8 -*-
 
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
 
class DiMajCodeDestWiz(models.TransientModel):
    _name = "di.majcodedestwiz_wiz"
    _description = 'Mise à jour codes destination'
    
    partner_ids = fields.Many2many("res.partner", string="Tiers")
     
    @api.model
    def default_get(self, fields):
        res = super(DiMajCodeDestWiz, self).default_get(fields)
        # récupération des enregistrements cochés                
        if not self.env.context["active_ids"]:
            raise ValidationError("Pas d'enregistrement selectionné")
        res["partner_ids"] = self.env.context["active_ids"]
        return res

    @api.multi
    def di_maj_codedest(self):
        # parcours des tiers à mettre à jour 
        for partner in self.partner_ids:
            partner._compute_code_dest()
            fils_ids = self.env['res.partner'].search([('parent_id','=',partner.id)])
            for fils in fils_ids:
                fils._compute_code_dest()
        res = self.message = "Génération terminée."        
        return res
