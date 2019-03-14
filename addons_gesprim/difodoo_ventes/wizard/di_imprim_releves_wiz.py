
# -*- coding: utf-8 -*-

from odoo import api, fields, models
from datetime import date, timedelta, datetime
from odoo.exceptions import ValidationError


class DiImpRelWiz(models.TransientModel):
    _name = "di.imp.rel.wiz"
    _description = "Wizard d'impression des relevés"
        
    di_date_releve = fields.Date(string="Date d'impression du relevé", required=True)
    di_reimp = fields.Boolean("Réimpression", default=False)
   
    di_demande = fields.Boolean("A la demande", default=True)
    di_jour = fields.Boolean("Jour", default=True)
    di_semaine = fields.Boolean("Semaine", default=True)
    di_decade = fields.Boolean("Décade", default=True)
    di_quinzaine = fields.Boolean("Quinzaine", default=True)
    di_mois = fields.Boolean("Mois", default=True)
    
    di_cli_deb = fields.Char("Client début")
    di_cli_fin = fields.Char("Client fin")
    di_fac_deb = fields.Char("Facture début")
    di_fac_fin = fields.Char("Facture fin")
    
    di_date_deb = fields.Date(string="Date Début")
    di_date_fin = fields.Date(string="Date fin")
    
    di_rlv_deb = fields.Integer("Relevé début")
    di_rlv_fin = fields.Integer("Relevé fin")
    
    di_rlv_ids = fields.Many2many('di.releve', string='Relevés')   
    
    
    def di_prepare_releves(self,listereleves,date_releve):
        releves = self.env['di.releve']
        
        for rlvno in listereleves:
            fac_ids = self.env['account.invoice'].search([('di_rlvno','=',rlvno)])
            for fac in fac_ids:
                partner_id = fac.partner_id.id
                break
                
            releves = releves + self.env['di.releve'].create({'di_date_releve': date_releve,'di_rlvno':rlvno,'di_fac_ids':[ (6, 0 , fac_ids.ids ) ],'di_partner_id':partner_id})
        return releves
            
    
    @api.multi
    def imprimer_releves(self):  
        
        datedeb =  self.di_date_deb.strftime('%Y-%m-%d')
        datefin =  self.di_date_fin.strftime('%Y-%m-%d')    
        
        
        if not self.di_fac_deb:
            self.di_fac_deb =''
        if not self.di_cli_deb:
            self.di_cli_deb =''
        
        if self.di_reimp:
            sqlstr = """
                    select ai.id                             
                    from account_invoice ai
                    left join res_partner cli on cli.id = ai.partner_id
                    where ai.type in ('out_invoice','out_refund') and ai.state not in ('draft','cancel') and ai.di_rlvno<>0 
                    and ai.di_rlvno between %s and %s 
                    and cli.ref between %s and %s 
                    and ai.date_invoice between %s and %s
                   order by ai.di_rlvno
                    """
           
            self.env.cr.execute(sqlstr, (self.di_rlv_deb, self.di_rlv_fin,self.di_cli_deb, self.di_cli_fin, datedeb, datefin))

        else:
            sqlstr = """
                    select ai.id                             
                    from account_invoice ai
                    left join res_partner cli on cli.id = ai.partner_id
                    where ai.type in ('out_invoice','out_refund') and ai.state not in ('draft','cancel') and ai.di_rlvno=0 
                    and ai.number between %s and %s 
                    and cli.ref between %s and %s 
                    and ai.date_invoice between %s and %s
                    and (
                    cli.di_type_releve = 'JOUR' and %s = '1'
                    or cli.di_type_releve = 'SEMAINE' and %s = '1'
                    or cli.di_type_releve = 'QUINZAINE' and %s = '1'
                    or cli.di_type_releve = 'DECADE' and %s = '1'
                    or cli.di_type_releve = 'MOIS' and %s = '1'
                    or cli.di_type_releve = 'DEMANDE' and %s = '1'
                    )
                    """
            if self.di_jour:
                jour = '1'
            else:
                jour = '0'
                
            if self.di_semaine:
                semaine = '1'
            else:
                semaine = '0'
            if self.di_decade:
                decade = '1'
            else:
                decade = '0'
            if self.di_quinzaine:
                quinzaine = '1'
            else:
                quinzaine = '0'
            if self.di_mois:
                mois = '1'
            else:
                mois = '0'
            if self.di_demande:
                demande = '1'
            else:
                demande = '0'  
            
            self.env.cr.execute(sqlstr, (self.di_fac_deb, self.di_fac_fin,self.di_cli_deb, self.di_cli_fin, datedeb, datefin,jour,semaine,quinzaine,decade,mois,demande))
                    
                                 
            
        result = self.env.cr.fetchall()
#             res['di_col_stock'] = result[0] 
        ids = []
        
        for tuple in result:
            ids.append(tuple[0])
            
        di_fac_ids=self.env['account.invoice'].browse(ids).sorted(key= lambda f: (f.partner_id.id)) 
#         di_fac_ids = di_fac_ids.sorted(key= lambda f: (f.partner_id.id)) 
        if not self.di_reimp:                                           
            cli_id = 0
            for fac in di_fac_ids:
                if cli_id != fac.partner_id.id:
                    param = self.env['di.param'].search([('di_company_id','=',self.env.user.company_id.id)])
                    if not param.di_rlvno:
                         param.di_rlvno = 0
                    rlvno = param.di_rlvno + 1
                    param.update({'di_rlvno':rlvno})                     
                fac.update({'di_rlvno':rlvno})
                cli_id = fac.partner_id.id
        
#         di_fac_ids=self.env['account.invoice'].browse(ids).sorted(key= lambda f: (f.di_rlvno))   
        lstrlvno = []        
        for fac in di_fac_ids:
            lstrlvno.append(fac.di_rlvno)
            
        lstrlvno=list(set(lstrlvno))
        
        self.di_rlv_ids = self.di_prepare_releves(lstrlvno,self.di_date_releve) 
        if self.di_rlv_ids:                                                                                    
            return self.env.ref('difodoo_ventes.di_action_report_releves').report_action(self)
        else:
            return False                                                       
            
    @api.model
    def default_get(self, fields):
        res = super(DiImpRelWiz, self).default_get(fields) 
        res["di_date_releve"] = datetime.today().date()
        res["di_cli_deb"] = ' '
        res["di_cli_fin"] = 'ZZZZZZZZZZ'
        res["di_fac_deb"] = ' '
        res["di_fac_fin"] = 'ZZZZZZZZZZZZZ'
        res["di_date_deb"] = datetime.strptime("01/01/1900","%d/%m/%Y").date()
        res["di_date_fin"] = datetime.strptime("31/12/2099","%d/%m/%Y").date()
        res["di_rlv_deb"] = 0
        res["di_rlv_fin"] = 9999999 
                                                                              
        return res    
