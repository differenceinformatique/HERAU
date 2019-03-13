
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
    
    di_fac_ids = fields.Many2many("account.invoice")
       
    
    @api.multi
    def imprimer_releves(self):  
        
        if self.di_reimp:
             sqlstr = """"""
        else:
            sqlstr = """
                    select id                             
                    from account_invoice ai
                    LEFT JOIN ( SELECT sloc.id,sloc.usage FROM stock_location sloc) stock_type ON stock_type.id = sml.location_dest_id
                    LEFT JOIN ( SELECT sloc.id,sloc.usage FROM stock_location sloc) orig_type ON orig_type.id = sml.location_id
                    LEFT JOIN (select di_cout.di_cmp,di_cout.id,di_cout.di_product_id from di_cout order by di_date desc limit 1) cmp on cmp.di_product_id = sml.product_id
                    LEFT JOIN stock_move sm on sm.id = sml.move_id
                    LEFT JOIN (select sol.price_unit, sol.id from sale_order_line sol) sol on sol.id = sm.sale_line_id                 
                    where sml.product_id = %s and sml.state ='done' and sml.date <=%s and sml.di_flg_cloture is not true
                    """
            
            self.env.cr.execute(sqlstr, (val.id, di_date_to))
            result = self.env.cr.fetchall()[0]
            res[val.id]['di_col_stock'] = result[0] and result[0] or 0.0
        
                                                         
        return self.env.ref('difodoo_ventes.di_action_report_releves').report_action(self)                                                       
            
    @api.model
    def default_get(self, fields):
        res = super(DiImpRelWiz, self).default_get(fields) 
        res["di_date_releve"] = datetime.today().date()
        res["di_cli_deb"] = ''
        res["di_cli_fin"] = 'ZZZZZZZZZZ'
        res["di_fac_deb"] = ''
        res["di_fac_fin"] = 'ZZZZZZZZZZZZZ'
        res["di_date_deb"] = datetime.strptime("01/01/1900","%d/%m/%Y")
        res["di_date_fin"] = datetime.strptime("31/12/9999","%d/%m/%Y")
        res["di_rlv_deb"] = 0
        res["di_rlv_fin"] = 9999999999 
                                                                              
        return res    
