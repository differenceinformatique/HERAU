
# -*- coding: utf-8 -*-

from odoo import api, fields, models
from datetime import date, timedelta, datetime
from odoo.exceptions import ValidationError
from odoo.exceptions import Warning


class DiGenTarWiz(models.TransientModel):
    _name = "di.gen.tar.wiz"
    _description = "Wizard de génération de Tarifs de vente"
    
    di_tarif_orig_id = fields.Many2one("di.code.tarif", string="Code tarif origine", required=True)
    di_date_effet_orig = fields.Date(string="Date d'effet", required=True)
    di_date_effet = fields.Date(string="Date d'effet", required=True)
    di_date_fin = fields.Date(string="Date de fin")
    di_tarifs_dest_ids = fields.Many2many("di.code.tarif")
    
    @api.multi
    def generer_tarifs(self):
        # parcours des codes tarifs  destinationsélectionnés
        for tarifdest in self.di_tarifs_dest_ids:
            if tarifdest.id != self.di_tarif_orig_id.id: # on vérifie que le code tarif destination n'est pas le tarif d'origine
                for tarif_origine in self.env["di.tarifs"].search(['&',('di_code_tarif_id', '=', self.di_tarif_orig_id.id),('di_date_effet','=',self.di_date_effet_orig)]): 
                    #parcours de tarifs origine correspondants au code tarif et à la date d'effet sélectionnée   
                    #chargement des données du nouveau tarif                
                    data = {
                            'di_product_id': tarif_origine.di_product_id.id,
                            'di_code_tarif_id': tarifdest.id,
                            'di_partner_id': tarif_origine.di_partner_id.id,
                            'di_un_prix': tarif_origine.di_un_prix,
                            'di_type_colis_id': tarif_origine.di_type_colis_id,
                            'di_type_palette_id': tarif_origine.di_type_palette_id,
                            'di_prix': tarif_origine.di_prix * tarifdest.di_coef,
                            'di_qte_seuil': tarif_origine.di_qte_seuil,
                            'di_date_effet': self.di_date_effet,
                            'di_date_fin': self.di_date_fin                                  
                            }                       
                    #recherche si tarif existant                                    
                    tarif_existant = self.env["di.tarifs"].search(['&',('di_code_tarif_id', '=', tarifdest.id),
                                                                   ('di_date_effet','=',self.di_date_effet),
                                                                   ('di_company_id','=',self.env.user.company_id.id),
                                                                   ('di_product_id','=',tarif_origine.di_product_id.id),
                                                                   ('di_partner_id','=',tarif_origine.di_partner_id.id),                                                                   
                                                                   ('di_un_prix','=',tarif_origine.di_un_prix),
                                                                   ('di_type_colis_id','=', tarif_origine.di_type_colis_id.id),
                                                                   ('di_type_palette_id','=', tarif_origine.di_type_palette_id),
                                                                   ('di_qte_seuil','=',tarif_origine.di_qte_seuil)
                                                                   ])
                    
                    if tarif_existant:
                        # si il existe, on le met à jour
                        tarif_existant.update(data)     
                    else:
                        #sinon on le créé
                        self.env["di.tarifs"].create(data)  
       # raise Warning("Traitement terminé")  
        return self.env['di.popup.wiz'].afficher_message("Traitement terminé.",True,False,False,False)  
                                                           
            
    @api.model
    def default_get(self, fields):
        res = super(DiGenTarWiz, self).default_get(fields) 
        if self.env.context.get('active_model'): # on vérifie si on est dans un model
            active_model=self.env.context['active_model'] #récup du model courant
        else:
            active_model=''
        if active_model :    
            if active_model == 'di.code.tarif': # si lancé à partir des codes tarifs
                tarif_id = self.env.context["active_id"]
                Tarif = self.env["di.code.tarif"].browse(tarif_id)
                res["di_tarif_orig_id"] = Tarif.id
            elif active_model=='di.tarifs': # si lancé à partir des tarifs
                tarif_id = self.env.context["active_id"]
                Tarif = self.env["di.tarifs"].browse(tarif_id)
                res["di_tarif_orig_id"] = Tarif.di_code_tarif_id.id                                            
                res["di_date_effet_orig"] = Tarif.di_date_effet
                res["di_date_effet"] = Tarif.di_date_effet
                res["di_date_fin"] = Tarif.di_date_fin                                  
        else: # lancé à partir du menu
            res["di_date_effet_orig"] = datetime.today()      # je charge la date à aujourd'hui car si rien n'est envoyé, le wizard ne s'ouvre pas                               
        return res    