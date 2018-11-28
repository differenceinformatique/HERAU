# -*- coding: utf-8 -*-
from odoo import api, fields, models
from datetime import timedelta, datetime
import io
# import os
import base64
# from ..models import di_outils
# from pip._internal import download
from odoo.tools import pycompat

class Wizard_transfert_compta(models.TransientModel):
    _name = "di.transfertcompta.wiz"
    _description = "Wizard transfert compta"
    
    date_start = fields.Date('Start Date', help="Starting date for the creation of invoices", default=lambda self: self._default_start())
    date_end = fields.Date('End Date', help="Ending valid for the the creation of invoices", default=lambda self: fields.Date.today())
    journal_ids = fields.Many2many(comodel_name='account.journal', string="Journals", default=lambda self: self.env['account.journal'].search([('type', 'in', ['sale', 'purchase'])]), required=True)        
    writing_file_transfer = fields.Char(string='File For Writing Transfer', default=lambda self : self.env['di.param'].search([('di_company_id', '=', self.env.user.company_id.id)]).di_nom_exp_ecr_compta)
    compta_data = fields.Binary('Compta File', readonly=True)
    filename = fields.Char(string='Filename', size=256, readonly=True)            
        
        
    def replace_accent(self, s):
        if s:
            s = s.replace('ê', 'e') \
                 .replace('è', 'e') \
                 .replace('é', 'e') \
                 .replace('à', 'a') \
                 .replace('ô', 'o') \
                 .replace('ö', 'o') \
                 .replace('î', 'i')
        return s                 


    @api.model
    def _default_start(self):        
        start = datetime.today() + timedelta(days=-7)
        return fields.Date.context_today(self, timestamp=start)   
    
    def di_ecrire_ligne_divalto(self, move_name, journal, compte, partner_name, move_line_name, date_ecr, date_ech, debit, credit, currency, di_dos_compt, di_etb_compt):
        listrow = list()        
        libelle = ""
        n_piece = ""
                
        compte_gen = compte
        
        if move_line_name == "/":
            if partner_name:
                libelle = partner_name
        else:
            if move_line_name:
                libelle = move_line_name  
        
        libelle = self.replace_accent(libelle)
                         
        if move_name:
            n_piece = move_name
                
        if debit == 0:
            montant = credit
            sens = "1"
        else:         
            montant = debit
            sens = "2"
        
        ce1 = "8"
        
        if di_dos_compt:
            dos = di_dos_compt
        else:
            dos = ""
            
        ce2 = "1"
        
        if di_etb_compt:
            etb = di_etb_compt
        else:
            etb = ""
            
        ecrno = ""
        ecrlg = ""
        axe1 = ""
        axe2 = ""
        axe3 = ""
        axe4 = ""
        cp = ""
        reg = ""
        lett = ""
        point = ""
        lot = ""
        chqno = ""
        regtyp = ""
        mtbis = ""
        lettdt = ""
        pointdt = ""
        ecrvalno = ""
        devp = ""
        cptcol = ""
        natpai = ""
     
        listrow.append("{}".format(ce1))
        listrow.append("{}".format(dos))
        listrow.append( "{}".format(ce2))
        listrow.append( "{}".format(etb))
        listrow.append( "{}".format(compte_gen))
        listrow.append( "{}".format(date_ecr))
        listrow.append( "{}".format(libelle))
        listrow.append( "{}".format(journal))         
        listrow.append( "{}".format(ecrno))
        listrow.append( "{}".format(ecrlg))
        listrow.append( "{}".format(axe1))
        listrow.append( "{}".format(axe2))
        listrow.append( "{}".format(axe3))
        listrow.append( "{}".format(axe4))
        listrow.append( "{}".format(cp))
        listrow.append( "{}".format(reg))
        listrow.append( "{}".format(lett))
        listrow.append( "{}".format(point))
        listrow.append( "{}".format(lot))
        listrow.append( "{}".format(n_piece))
        listrow.append( "{}".format(date_ech))
        listrow.append( "{}".format(chqno))
        listrow.append( "{}".format(currency))
        listrow.append( "{}".format(regtyp)) # aml.payment_id.paymentmethod_id.code ???
        listrow.append( "{}".format(n_piece))  # pinotiers
        listrow.append( "{0:.2f}".format(montant))
        listrow.append( "{0:.2f}".format(montant))
        listrow.append( "{}".format(mtbis))
        listrow.append( "{}".format(sens))
        listrow.append( "{}".format(lettdt))
        listrow.append( "{}".format(pointdt))
        listrow.append( "{}".format(devp))
        listrow.append( "{}".format(ecrvalno))
        listrow.append( "{}".format(cptcol))
        listrow.append( "{}".format(natpai))
        return listrow
    
    @api.multi
    def transfert_compta(self):
        self.ensure_one()  
        param = self.env['di.param'].search([('di_company_id', '=', self.env.user.company_id.id)])
#         date_d = self.date_start[0:4] + self.date_start[5:7] + self.date_start[8:10] 
#         date_f = self.date_end[0:4] + self.date_end[5:7] + self.date_end[8:10] 
        date_d=self.date_start.strftime('%Y%m%d')
        date_f=self.date_end.strftime('%Y%m%d')
        
        
        compta_file = io.BytesIO()
        w = pycompat.csv_writer(compta_file, delimiter=';')
      
        # Transfert Invoices

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
                WHERE am.state = 'posted' 
                AND to_char(am.date,'YYYYMMDD') BETWEEN %s AND %s
                AND am.journal_id IN %s
                AND aml.di_transfere is not true
                ORDER BY account_journal.code, am.id, account_account.code"""

        self.env.cr.execute(sql, (date_d, date_f, tuple(self.journal_ids.ids),))
        
        nb_lig = 0
        ids = [(r[0], r[1], r[2], r[3], r[4], r[5], r[6], r[7], r[8], r[9], r[10]) for r in self.env.cr.fetchall()]
        for line_id, move_name, journal, compte, partner_name, move_line_name, date_ecr, date_ech, debit, credit, currency in ids:
            nb_lig += 1

            listrow = list()
                        
            if param.di_compta_prg == "DIVALTO":                               
                listrow = self.di_ecrire_ligne_divalto(move_name, journal, compte, partner_name, move_line_name, date_ecr, date_ech, debit, credit, currency, param.di_dos_compt, param.di_etb_compt)
                
            w.writerow(listrow)
            line = self.env['account.move.line'].browse(line_id)
            
            line.update({'di_transfere': True})

        comptavalue = compta_file.getvalue()
        self.write({
            'compta_data': base64.encodestring(comptavalue),            
            'filename': self.writing_file_transfer,
            })
        compta_file.close()
        action = {
            'name': 'di_transfert_compta',
            'type': 'ir.actions.act_url',
            'url': "web/content/?model=di.transfertcompta.wiz&id=" + str(self.id) + "&filename_field=filename&field=compta_data&download=true&filename=" + self.filename,
            'target': 'new',
            }
        return action                    