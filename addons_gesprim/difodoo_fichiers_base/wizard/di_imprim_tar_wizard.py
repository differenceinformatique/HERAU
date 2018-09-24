
# -*- coding: utf-8 -*-

from odoo import api, fields, models
from datetime import date, timedelta, datetime
from odoo.exceptions import ValidationError


class DiImpTarWiz(models.TransientModel):
    _name = "di.imp.tar.wiz"
    _description = "Wizard d'impression de Tarifs de vente"
        
    di_date_effet = fields.Date(string="Date d'application du tarif", required=True)    
    di_codes_tarifs_ids = fields.Many2many("di.code.tarif")
    di_category = fields.Many2one("product.category",string="Famille")
    di_notImp_Un_vide = fields.Boolean(string="Ne pas imprimer tarifs sans unité de prix.",default=True)
    
    di_tarifs_ids = fields.Many2many("di.tarifs")
    
    
    @api.multi
    def imprimer_tarifs(self):  
        
        if self.di_category:            
            listcateg=self.di_category.child_id.ids 
            listcateg.append(self.di_category.id)
              
            di_tarifs_ids = self.env['di.tarifs']\
            .search(['&', ('di_date_effet', '<=', self.di_date_effet), ('di_code_tarif_id', 'in', self.di_codes_tarifs_ids.ids), ('di_product_id.product_tmpl_id.categ_id', 'in', listcateg)])\
            .filtered(lambda t: (t.di_date_fin and t.di_date_fin >= self.di_date_effet) or not t.di_date_fin).ids#\
            
            
            di_tarifs_ids_obj = self.env['di.tarifs']\
            .search(['&', ('di_date_effet', '<=', self.di_date_effet), ('di_code_tarif_id', 'in', self.di_codes_tarifs_ids.ids), ('di_product_id.product_tmpl_id.categ_id', 'in', listcateg)])\
            .filtered(lambda t: (t.di_date_fin and t.di_date_fin >= self.di_date_effet) or not t.di_date_fin)
        else:
            di_tarifs_ids = self.env['di.tarifs']\
            .search(['&', ('di_date_effet', '<=', self.di_date_effet), ('di_code_tarif_id', 'in', self.di_codes_tarifs_ids.ids)])\
            .filtered(lambda t: (t.di_date_fin and t.di_date_fin >= self.di_date_effet) or not t.di_date_fin).ids#\
            
            
            di_tarifs_ids_obj = self.env['di.tarifs']\
            .search(['&', ('di_date_effet', '<=', self.di_date_effet), ('di_code_tarif_id', 'in', self.di_codes_tarifs_ids.ids)])\
            .filtered(lambda t: (t.di_date_fin and t.di_date_fin >= self.di_date_effet) or not t.di_date_fin)
            
        if self.di_notImp_Un_vide:
            di_tarifs_ids_obj=di_tarifs_ids_obj.filtered(lambda t: (t.di_un_prix!=False and t.di_un_prix!=''))
        ok = False
        
        
        while ok == False:
            ok=True
            for id1 in di_tarifs_ids :
                tid = self.env['di.tarifs'].browse(id1)
                for id2 in di_tarifs_ids :
                    tid2 = self.env['di.tarifs'].browse(id2)
                    if tid2.id != tid.id and tid2.di_code_tarif_id == tid.di_code_tarif_id and tid2.di_product_id == tid.di_product_id and ((tid2.di_un_prix == tid.di_un_prix)or(tid2.di_prix ==tid.di_prix and not tid.di_un_prix and tid2.di_un_prix)) and tid2.di_date_effet <= tid.di_date_effet:
                        di_tarifs_ids.remove(id2)
                        ok=False
                    
                
#         newtar = self.env['di.tarifs'].new()
#         self.di_tarifs_ids = di_tarifs_ids
#         for idt in di_tarifs_ids:
#             newtar.(self.env['di.tarifs'].browse(idt))            
        self.di_tarifs_ids = di_tarifs_ids_obj
        
        for tar in  self.di_tarifs_ids:
            if tar.id not in  di_tarifs_ids:
                tar.unlink()                                                      
        return self.env.ref('difodoo_fichiers_base.di_action_report_tarifs').report_action(self)                                                       
            
    @api.model
    def default_get(self, fields):
        res = super(DiImpTarWiz, self).default_get(fields) 
        res["di_date_effet"] = datetime.today()
        if self.env.context.get('active_model'):  # on vérifie si on est dans un model
            active_model = self.env.context['active_model']  # récup du model courant
        else:
            active_model = ''
        code_tarif_ids = []            
        if active_model == 'di.code.tarif':  # si lancé à partir des codes tarifs
            code_tarif_ids = self.env.context["active_ids"]            
            
        elif active_model == 'di.tarifs':  # si lancé à partir des tarifs
            
            tarif_ids = self.env.context["active_ids"]
            for tarif_id in tarif_ids:
                Tarif = self.env["di.tarifs"].browse(tarif_id)
                code_tarif_ids.append(Tarif.di_code_tarif_id.id)
                
        if code_tarif_ids:            
            res["di_codes_tarifs_ids"] = code_tarif_ids    
                                                                              
        return res    
