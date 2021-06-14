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
    journal_ids = fields.Many2many(comodel_name='account.journal', string="Journals", default=lambda self: self.env['account.journal'].search([('type', 'in', ['sale', 'purchase','cash','bank'])]), required=True)        
    writing_file_transfer = fields.Char(string='File For Writing Transfer', default=lambda self : self.env['di.param'].search([('di_company_id', '=', self.env.user.company_id.id)]).di_nom_exp_ecr_compta)
    compta_data = fields.Binary('Compta File', readonly=True)
    filename = fields.Char(string='Filename', size=256, readonly=True)     
    di_reexporter = fields.Boolean("Réexporter les écritures déjà transférées.", default=False)          
        
        
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
        
        # temporaire herau, compte par défaut adresse manuelle (client divers)
        if compte=='411100':
            compte = 'C0009999'
            libelle = 'DIVERS'
                
        compte_gen = compte
        
        if move_line_name == "/":
            if partner_name:
                libelle = partner_name
        else:
            if move_line_name:
                libelle = move_line_name  
        
        libelle = self.replace_accent(libelle)
        
        # temporaire herau, pas le n° de pièce pour les caisses
        if journal[0] == 'T':
            move_name = ''
                         
        if move_name:
            n_piece = move_name.rjust(20)   # ajout d'espaces devant pour compléter à 20 caractères.
        if debit > credit:
            sens = "1"
            montant = debit - credit
        else:
            sens = "2"
            montant = credit-debit
                
        # if debit == 0:
        #     # crédit
        #     montant = credit
        #     sens = "2"
        # else:
        #     # débit         
        #     montant = debit
        #     sens = "1"
        
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
        if self.di_reexporter:
            sql = """SELECT am.name as move_name, account_journal.code as journal,account_account.code as compte,
                    res_partner.name as partner, account_account.name as libelle,
                    to_char(am.date,'YYYYMMDD') as date_ecr,
                    to_char(aml.date_maturity,'YYYYMMDD') as date_ech,
                    sum(aml.debit), sum(aml.credit), res_currency.name as currency
                    from account_move_line as aml
                    INNER JOIN account_move as am on am.id = aml.move_id
                    INNER JOIN account_journal on account_journal.id = am.journal_id
                    INNER JOIN res_currency on res_currency.id = am.currency_id
                    INNER JOIN res_partner on res_partner.id = am.partner_id 
                    INNER JOIN account_account on account_account.id = aml.account_id                
                    WHERE am.state = 'posted' 
                    AND to_char(am.date,'YYYYMMDD') BETWEEN %s AND %s
                    AND am.journal_id IN %s                    
                    group by am.name, account_journal.code,account_account.code,
                    res_partner.name, account_account.name, am.date, aml.date_maturity,res_currency.name
                    ORDER BY account_journal.code, am.name, account_account.code"""
        else:
            
            sql = """SELECT am.name as move_name, account_journal.code as journal,account_account.code as compte,
                    res_partner.name as partner, account_account.name as libelle,
                    to_char(am.date,'YYYYMMDD') as date_ecr,
                    to_char(aml.date_maturity,'YYYYMMDD') as date_ech,
                    sum(aml.debit), sum(aml.credit), res_currency.name as currency
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
                    group by am.name, account_journal.code,account_account.code,
                    res_partner.name, account_account.name, am.date, aml.date_maturity,res_currency.name
                    ORDER BY account_journal.code, am.name, account_account.code"""

        self.env.cr.execute(sql, (date_d, date_f, tuple(self.journal_ids.ids),))
        
        listrow_entete = list()
        listrow_entete.append("{}".format('ce1'))
        listrow_entete.append("{}".format('dos'))
        listrow_entete.append( "{}".format('ce2'))
        listrow_entete.append( "{}".format('etb'))
        listrow_entete.append( "{}".format('cpt'))
        listrow_entete.append( "{}".format('ecrdt'))
        listrow_entete.append( "{}".format('lib'))
        listrow_entete.append( "{}".format('jnl'))         
        listrow_entete.append( "{}".format('ecrno'))
        listrow_entete.append( "{}".format('ecrlg'))
        listrow_entete.append( "{}".format('axe(1)'))
        listrow_entete.append( "{}".format('axe(2)'))
        listrow_entete.append( "{}".format('axe(3)'))
        listrow_entete.append( "{}".format('axe(4)'))
        listrow_entete.append( "{}".format('cp'))
        listrow_entete.append( "{}".format('reg'))
        listrow_entete.append( "{}".format('lett'))
        listrow_entete.append( "{}".format('point'))
        listrow_entete.append( "{}".format('lot'))
        listrow_entete.append( "{}".format('piece'))
        listrow_entete.append( "{}".format('echdt'))
        listrow_entete.append( "{}".format('chqno'))
        listrow_entete.append( "{}".format('dev'))
        listrow_entete.append( "{}".format('regtyp')) 
        listrow_entete.append( "{}".format('pinotiers')) 
        listrow_entete.append( "{}".format('mt'))
        listrow_entete.append( "{}".format('mtdev'))
        listrow_entete.append( "{}".format('mtbis'))
        listrow_entete.append( "{}".format('sens'))
        listrow_entete.append( "{}".format('lettdt'))
        listrow_entete.append( "{}".format('pointdt'))
        listrow_entete.append( "{}".format('devp'))
        listrow_entete.append( "{}".format('ecrvalno'))
        listrow_entete.append( "{}".format('cptcol'))
        listrow_entete.append( "{}".format('natpai'))
        w.writerow(listrow_entete)
        
        nb_lig = 0
        ids = [(r[0],r[1], r[2], r[3], r[4], r[5], r[6], r[7], r[8], r[9]) for r in self.env.cr.fetchall()]
        for move_name, journal, compte, partner_name, move_line_name, date_ecr, date_ech, debit, credit, currency in ids:
            nb_lig += 1

            listrow = list()
                        
            if param.di_compta_prg == "DIVALTO":                               
                listrow = self.di_ecrire_ligne_divalto(move_name, journal, compte, partner_name, move_line_name, date_ecr, date_ech, debit, credit, currency, param.di_dos_compt, param.di_etb_compt)
                
            w.writerow(listrow)
            
            
        sql = """SELECT aml.id
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
                ORDER BY account_journal.code, am.name, account_account.code"""

        self.env.cr.execute(sql, (date_d, date_f, tuple(self.journal_ids.ids),))
        ids = [(r[0]) for r in self.env.cr.fetchall()]
        for id in ids:    
            line = self.env['account.move.line'].browse(id)
            
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