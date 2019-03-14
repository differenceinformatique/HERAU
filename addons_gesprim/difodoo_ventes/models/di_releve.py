
# -*- coding: utf-8 -*-

from odoo import api, fields, models
from datetime import date, timedelta, datetime, time
from odoo.exceptions import ValidationError


class DiReleve(models.TransientModel):
    _name = "di.releve"
    _description = "Modèle temporaire de relevé pour impression"
     
    di_company_id = fields.Many2one('res.company', string='Société', readonly=True,  default=lambda self: self.env.user.company_id)   
    di_date_releve = fields.Date(string="Date d'impression du relevé")   
    di_fac_ids = fields.Many2many('account.invoice', string='Factures')   
    di_rlvno = fields.Integer("Numéro de relevé")  
    di_partner_id = fields.Many2one('res.partner', string='Client')
    
    @api.model
    def _get_date_ech(self):
        dateech=datetime.today().date()
        for term in self.di_partner_id.property_payment_term_id.line_ids:            
            dateech = self.di_date_releve + timedelta(days=term.days)
            if term.day_of_the_month:
                if dateech.day > term.day_of_the_month:
                    dateech = dateech + timedelta(month=1)                
#                 dateech.replace(day= term.day_of_the_month)
            break
        return dateech