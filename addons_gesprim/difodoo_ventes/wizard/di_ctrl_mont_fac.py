
# -*- coding: utf-8 -*-

from odoo import api, fields, models
from datetime import date, timedelta, datetime
from odoo.exceptions import ValidationError


class DiCtrlMontFac(models.TransientModel):
    _name = "di.ctrl.mont.fac"
    _description = "Wizard de contrôle des montants de facture"
    
    di_company_id = fields.Many2one('res.company', string='Société', readonly=True,  default=lambda self: self.env.user.company_id)            
    di_aol_ids = fields.Many2many("account.invoice.line")
    
    
    @api.multi
    def controle_montants(self):  
        req="""
            select id from account_invoice_line 
                where 
                (di_un_prix = 'KG' and  
                 (
                     price_subtotal - ((price_unit * cast(di_poin as numeric)) * (1-(discount/100))) not between -0.005 and 0.005
                 )
                )
                or
                (di_un_prix = 'PIECE' and  
                 (
                     price_subtotal - ((price_unit * cast(di_nb_pieces as numeric)) * (1-(discount/100))) not between -0.005 and 0.005
                 )
                )or
                (di_un_prix = 'COLIS' and  
                 (
                     price_subtotal - ((price_unit * cast(di_nb_colis as numeric)) * (1-(discount/100))) not between -0.005 and 0.005
                 )
                )
        """
        
        self._cr.execute(req)
        aol_ids = (x[0] for x in self._cr.fetchall())
        if aol_ids:
            self.di_aol_ids = self.env['account.invoice.line'].browse(aol_ids)
                                                                            
        return self.env.ref('difodoo_ventes.di_action_report_ctrl_mont_fac').report_action(self)
                                                             
            
    @api.model
    def default_get(self, fields):
        res = super(DiCtrlMontFac, self).default_get(fields)                         
        return res    
