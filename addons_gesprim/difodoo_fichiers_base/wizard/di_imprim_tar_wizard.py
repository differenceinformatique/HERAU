
# -*- coding: utf-8 -*-

from odoo import api, fields, models
from datetime import date, timedelta, datetime
from odoo.exceptions import ValidationError


class DiImpTarWiz(models.TransientModel):
    _name = "di.imp.tar.wiz"
    _description = "Wizard d'impression de Tarifs de vente"
        
    di_date_effet = fields.Date(string="Date d'application du tarif", required=True)    
    di_codes_tarifs_ids = fields.Many2many("di.code.tarif")
    
    di_tarifs_ids = fields.Many2many("di.tarifs")
    
    
    @api.multi
    def imprimer_tarifs(self):  
        di_tarifs_ids=[]
                      
        
        query_args = {'di_codes_tarifs_ids' : self.di_codes_tarifs_ids.ids,'di_date':self.di_date_effet}
        query = """ SELECT  id 
                        FROM di_tarifs                         
                        WHERE di_code_tarif_id in (""" + ','.join(map(str, self.di_codes_tarifs_ids.ids)) + """ )                                                   
                        AND di_date_effet <= %(di_date)s
                        AND 
                        (di_date_fin >= %(di_date)s OR di_date_fin is null)
                        ORDER BY di_product_id asc,di_un_prix asc,di_date_effet desc,di_qte_seuil desc                            
                        """

        self.env.cr.execute(query, query_args)
        di_tarifs_ids = [(r[0]) for r in self.env.cr.fetchall()]
        
        
        #r= self.env.cr.fetchall()
#         self.di_tarifs_ids.ids = di_tarifs_ids
        for di_tarif_id in di_tarifs_ids:
            self.write({"di_tarifs_ids":[(4,di_tarif_id)]})
#              self.di_tarifs_ids.__add__(self.env['di.tarifs'].browse(di_tarif_id))
                                                                    
        return self.env.ref('difodoo_fichiers_base.di_action_report_tarifs').report_action(self)#                                                       
            
    @api.model
    def default_get(self, fields):
        res = super(DiImpTarWiz, self).default_get(fields) 
        res["di_date_effet"] = datetime.today()
        if self.env.context.get('active_model'): # on vérifie si on est dans un model
            active_model=self.env.context['active_model'] #récup du model courant
        else:
            active_model=''
        code_tarif_ids=[]            
        if active_model == 'di.code.tarif': # si lancé à partir des codes tarifs
            code_tarif_ids = self.env.context["active_ids"]            
            
        elif active_model=='di.tarifs': # si lancé à partir des tarifs
            
            tarif_ids = self.env.context["active_ids"]
            for tarif_id in tarif_ids:
                Tarif = self.env["di.tarifs"].browse(tarif_id)
                code_tarif_ids.append(Tarif.di_code_tarif_id.id)
                
        if code_tarif_ids:            
            res["di_codes_tarifs_ids"] = code_tarif_ids    
                                                                              
        return res    