# -*- coding: utf-8 -*-
from odoo import api, fields, models
from datetime import timedelta, datetime
import io
import os

from ..models import di_outils

class Wizard_transfert_compta(models.TransientModel):
    _name = "di.transfertcompta.wiz"
    _description = "Wizard transfert compta"
    
    date_start = fields.Date('Start Date', help="Starting date for the creation of invoices", default=lambda self: self._default_start())
    date_end = fields.Date('End Date', help="Ending valid for the the creation of invoices", default=lambda self: fields.Date.today())
    journal_ids = fields.Many2many(comodel_name='account.journal', string="Journals", default=lambda self: self.env['account.journal'].search([('type', 'in', ['sale', 'purchase'])]), required=True)
    path_account_transfer = fields.Char(string='Path For Account Transfer', default=lambda self : self.env['di.param'].search([('di_company_id','=',self.env.user.company_id.id)]).di_chem_exp_compta)     
    writing_file_transfer = fields.Char(string='File For Writing Transfer',default=lambda self : self.env['di.param'].search([('di_company_id','=',self.env.user.company_id.id)]).di_nom_exp_ecr_compta)   
    
     
        
    @api.model
    def _default_start(self):        
        start = datetime.today() + timedelta(days=-7)
        return fields.Date.context_today(self, timestamp=start)   
    
    def di_ecrire_ligne_divalto(self,move_name, journal, compte, partner_name, move_line_name, date_ecr, date_ech, debit, credit, currency,di_dos_divalto,di_etb_divalto):        
        libelle = ""
        n_piece = ""
                
        compte_gen = compte
        
        if move_line_name == "/":
            if partner_name:
                libelle = partner_name
        else:
            if move_line_name:
                libelle = move_line_name  
        
        libelle = di_outils.replace_accent(self, libelle)
                         
        if move_name:
            n_piece = move_name
                
        if debit == 0:
            montant = credit
            sens = "1"
        else:         
            montant = debit
            sens = "2"
        
        ce1     = "8"
        
        if di_dos_divalto:
            dos = di_dos_divalto
        else:
            dos = ""
            
        ce2     = "1"
        
        if di_etb_divalto:
            etb = di_etb_divalto
        else:
            etb = ""
            
        ecrno   = ""
        ecrlg   = ""
        axe1    = ""
        axe2    = ""
        axe3    = ""
        axe4    = ""
        cp      = ""
        reg     = ""
        lett    = ""
        point   = ""
        lot     = ""
        chqno   = ""
        regtyp  = ""
        mtbis   = ""
        lettdt  = ""
        pointdt = ""
        ecrvalno= ""
        devp    = ""
        cptcol  = ""
        natpai  = ""
        
        csv_row = ""
        csv_row += "{};".format(ce1)
        csv_row += "{};".format(dos)
        csv_row += "{};".format(ce2)
        csv_row += "{};".format(etb)
        csv_row += "{};".format(compte_gen)
        csv_row += "{};".format(date_ecr)
        csv_row += "{};".format(libelle)
        csv_row += "{};".format(journal)            
        csv_row += "{};".format(ecrno)
        csv_row += "{};".format(ecrlg)
        csv_row += "{};".format(axe1)
        csv_row += "{};".format(axe2)
        csv_row += "{};".format(axe3)
        csv_row += "{};".format(axe4)
        csv_row += "{};".format(cp)
        csv_row += "{};".format(reg)
        csv_row += "{};".format(lett)
        csv_row += "{};".format(point)
        csv_row += "{};".format(lot)
        csv_row += "{};".format(n_piece)
        csv_row += "{};".format(date_ech)
        csv_row += "{};".format(chqno)
        csv_row += "{};".format(currency)
        csv_row += "{};".format(regtyp)
        csv_row += "{};".format(n_piece) #pinotiers
        csv_row += "{0:.2f};".format(montant)
        csv_row += "{0:.2f};".format(montant)
        csv_row += "{};".format(mtbis)
        csv_row += "{};".format(sens)
        csv_row += "{};".format(lettdt)
        csv_row += "{};".format(pointdt)
        csv_row += "{};".format(devp)
        csv_row += "{};".format(ecrvalno)
        csv_row += "{};".format(cptcol)
        csv_row += "{};".format(natpai)
        return csv_row
    @api.multi
    def transfert_compta(self):  
        param = self.env['di.param'].search([('di_company_id','=',self.env.user.company_id.id)])
        date_d = self.date_start[0:4] + self.date_start[5:7] + self.date_start[8:10] 
        date_f = self.date_end[0:4] + self.date_end[5:7] + self.date_end[8:10] 

        csv_path = self.path_account_transfer        
        writing_file = self.writing_file_transfer
            
        if csv_path is None:
            csv_path = os.environ.get('HOME') or os.getcwd()  # c:\odoo\odoo11

        if writing_file is None:    
            writing_file = 'ecritures.csv'
            
        csv_path = os.path.normpath(csv_path)    
        if not os.path.exists(csv_path): 
            os.makedirs(csv_path)
        os.chdir(csv_path)        
        
        # Transfert Invoices
        fpi = io.open(writing_file, 'w', encoding='utf-8')

        sql = """SELECT aml.id,am.name as move_name, account_journal.code as journal,account_account.code as compte,
                res_partner.name as partner, aml.name as move_line_name,
                to_char(am.date,'YYYYMMDD') as date_ecr,
                to_char(aml.date_maturity,'YYYYMMDD') as date_ech,
                aml.debit, aml.credit, res_currency.name as currency
                from account_move_line as aml
                INNER JOIN account_move as am on am.id = aml.move_id
                INNER JOIN account_journal on account_journal.id = am.journal_id
                INNER JOIN res_currency on res_currency.id = am.currency_id
                INNER JOIN res_partner on res_partner.id = am.partner_id 
                INNER JOIN account_account on account_account.id = aml.account_id 
                LEFT JOIN account_analytic_account as aaa on aaa.id = aml.analytic_account_id 
                WHERE am.state = 'posted' 
                AND to_char(am.date,'YYYYMMDD') BETWEEN %s AND %s
                AND am.journal_id IN %s
                AND aml.di_transfere is not true
                ORDER BY account_journal.code, am.id, account_account.code"""

        self.env.cr.execute(sql, (date_d, date_f, tuple(self.journal_ids.ids),))
        
        nb_lig = 0
        csv = ""
        ids = [(r[0], r[1], r[2], r[3], r[4], r[5], r[6], r[7], r[8], r[9],r[10]) for r in self.env.cr.fetchall()]
        for line_id,move_name, journal, compte, partner_name, move_line_name, date_ecr, date_ech, debit, credit, currency in ids:
            nb_lig += 1
            csv_row = "" 
            if param.di_compta_prg == "DIVALTO":                               
                csv_row = self.di_ecrire_ligne_divalto(move_name, journal, compte, partner_name, move_line_name, date_ecr, date_ech, debit, credit, currency,param.di_dos_divalto,param.di_etb_divalto)
                
            csv += "{}\n".format(csv_row[:-1])
            line = self.env['account.move.line'].browse(line_id)
            
            line.update({'di_transfere': True})
       
        fpi.write(csv)
        fpi.close()