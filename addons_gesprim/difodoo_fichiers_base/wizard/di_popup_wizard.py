
# -*- coding: utf-8 -*-

from odoo import api, fields, models
from datetime import date, timedelta, datetime
from odoo.exceptions import ValidationError
from odoo.exceptions import Warning


class DiPopupsWiz(models.TransientModel):
    _name = "di.popup.wiz"
    _description = "Wizard d'affichage de message"
    
    name = fields.Char('Message')    
    button_ok = fields.Boolean(default=True)
    button_yes = fields.Boolean(default=False)
    button_no = fields.Boolean(default=False)
    button_cancel = fields.Boolean(default=False)
    

    @api.multi
    def oui(self):
        return "oui"
    
    @api.multi
    def non(self):
        return "non"
    
    
    @api.multi
    def afficher_message(self,mess="Fin",bouton_ok=True,bouton_oui=False,bouton_non=False,bouton_annuler=False):
        return {
            'name':mess,            
            'button_ok':bouton_ok,
            'button_yes':bouton_oui,
            'button_no':bouton_non,
            'button_cancel':bouton_annuler,
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'di.popup.wiz',
            'target':'new' 
        }