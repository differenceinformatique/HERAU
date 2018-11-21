
# -*- coding: utf-8 -*-

from odoo import api, fields, models
from datetime import datetime
from odoo.exceptions import ValidationError

class DiPayerComWiz(models.TransientModel):
    _name = "di.payer.com.wiz"
    _description = "Wizard de paiement des commissions des courtiers"
    
#     di_date_deb = fields.Date(string="Date de début")
#     di_date_fin = fields.Date(string="Date de fin")
    
    @api.multi
    def di_generer_factures(self):
        for payer in self:
            sol = self.env['sale.order.line'].search(['&',('di_courtier_id','!=',False),('di_prc_com_court','!=',0.0),('di_flg_com','!=',True),('invoice_lines','!=',False),('invoice_lines.invoice_id.state','!=','cancel')]).sorted(key=lambda l: l.di_courtier_id)                 
            courtier = False
            montant = 0.0
            if sol:
                for line in sol:
                    if line.di_courtier_id != courtier and courtier!= False :   
                        payer.ecrire_facture(courtier,montant)
                        montant = 0.0                                                         
                    montant += sum([il.price_total for il in line.invoice_lines if il.price_subtotal_signed >=0.0])
                    montant -= sum([il.price_total for il in line.invoice_lines if il.price_subtotal_signed <0.0])                             
                    courtier = line.di_courtier_id                    
                payer.ecrire_facture(courtier,montant)
                sol.update({'di_flg_com':True})
        # TODO : flaguer les lignes de commandes

    def ecrire_facture(self,courtier,montant):      
        invoice = self.env['account.invoice']
        invoice_line = self.env['account.invoice.line']  
        data_invoice = { 
                'name':'Paiement commission '+datetime.today().date().strftime('%d/%m/%Y'),
                'reference':'Paiement commission '+datetime.today().date().strftime('%d/%m/%Y'),                
                'type': 'in_invoice',                
                'state': 'draft' ,
                'partner_id':courtier.id,
                'account_id':courtier.property_account_payable_id.id,
                'date_invoice':datetime.today().date()                         
                        }
                                 
        data_invoice_line={
                    'invoice_id':invoice.create(data_invoice).id,
                    'name':'Paiement commission',
                    'product_id': self.env.user.company_id.di_param_id.di_art_com.id,
                    'account_id': courtier.property_account_payable_id.id,                    
                    'uom_id':self.env.user.company_id.di_param_id.di_art_com.uom_id.id,
                    'di_un_prix':'PIECE',
                    'di_un_saisie':'PIECE',
                    'di_qte_un_saisie':1.0,
                    'di_nb_pieces':1.0,
                    'price_unit':montant,
                    'quantity':1.0,
                    'partner_id': courtier.id                            
                    }                                                                                                                                                                                                                                                                                   
                 
        invoice_line.create(data_invoice_line)
        
                                                                        
    @api.model
    def default_get(self, fields):        
        res = super(DiPayerComWiz, self).default_get(fields)
        
        if not self.env.user.company_id.di_param_id.di_art_com:
            raise ValidationError("L'article de commission n'est pas paramétré.")                                    
                                     
        return res  
               
