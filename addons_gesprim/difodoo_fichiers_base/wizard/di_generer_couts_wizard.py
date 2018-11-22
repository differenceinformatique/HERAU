
# -*- coding: utf-8 -*-

from odoo import api, fields, models
from datetime import date, timedelta, datetime
from odoo.exceptions import ValidationError
from odoo.exceptions import Warning


class DiGenCoutsWiz(models.TransientModel):
    _name = "di.gen.couts.wiz"
    _description = "Wizard de génération de couts"
    
    di_generer_tous_tar = fields.Boolean(string="Générer tous les tarifs ?",default=False)
    di_cde_ach = fields.Boolean(string="Prendre en compte les commandes d'achat dans le calcul.",default=False)
   
#     def afficher_message_fin(self):
#         return self.env['di.popup.wiz'].afficher_message("Traitement terminé.",True,False,False,False)
        
    def di_generer_cmp(self,di_product_id,di_date):
        
        cout_jour = self.env['di.cout'].search(['&', ('di_product_id', '=', di_product_id), ('di_date', '=', di_date)])
        
        if not cout_jour:
            premier_mouv_vente = self.env['sale.order.line'].new()
            premier_mouv_achat = self.env['purchase.order.line'].new()
            date_veille = di_date + timedelta(days=-1)
            
#             mouvs_achat = self.env['purchase.order.line'].search([('product_id','=',di_product_id)]).sorted('order_id.date_order')
            mouvs_achat = self.env['purchase.order.line'].search([('product_id','=',di_product_id)]).sorted(key=lambda m: m.order_id.date_order )
            for premier_mouv_achat in mouvs_achat:
                break
            mouvs_vente = self.env['sale.order.line'].search([('product_id','=',di_product_id)]).sorted(key=lambda m: m.order_id.date_order )
            for premier_mouv_vente in mouvs_vente:
                break
            
            if premier_mouv_achat.order_id.date_order and not premier_mouv_vente.order_id.date_order:
                premier_mouv = premier_mouv_achat
            elif premier_mouv_vente.order_id.date_order and not premier_mouv_achat.order_id.date_order:
                premier_mouv = premier_mouv_vente
            else:
                if premier_mouv_achat.order_id.date_order > premier_mouv_vente.order_id.date_order:
                    premier_mouv = premier_mouv_vente
                else:
                    premier_mouv = premier_mouv_achat
                              
            cout_veille = self.env['di.cout'].search(['&', ('di_product_id', '=', di_product_id), ('di_date', '=', date_veille)])
            
            qte = 0.0
            mont =0.0
            nbcol=0.0
            nbpal=0.0
            nbpiece=0.0
            poids=0.0
            (qte,mont,nbcol,nbpal,nbpiece,poids) = self.env['stock.move'].di_somme_quantites_montants(di_product_id,di_date,self.di_cde_ach)       
            if not cout_veille and premier_mouv.order_id.date_order and  date_veille >= premier_mouv.order_id.date_order.date() :
                self.di_generer_cmp(di_product_id,date_veille)
                cout_veille = self.env['di.cout'].search(['&', ('di_product_id', '=', di_product_id), ('di_date', '=', date_veille)])

            qte = cout_veille.di_qte + qte
            mont = cout_veille.di_mont+ mont
            nbcol = cout_veille.di_nbcol + nbcol
            nbpal = cout_veille.di_nbpal + nbpal
            nbpiece = cout_veille.di_nbpiece + nbpiece
            poids = cout_veille.di_poin + poids             
            if qte !=0.0:
                cmp=mont/qte
            else:
                nbcol = 0
                nbpal = 0
                nbpiece = 0
                poids = 0
                mont = 0
                cmp=mont
                
#             if  qte !=0.0 or mont != 0.0 or nbcol!=0.0 or nbpal!=0.0 or nbpiece!=0.0 or poids!=0.0:   
#                 self    
                    
            data ={
                        'di_date': di_date,  
                        'di_product_id' : di_product_id,
                        'di_qte' : qte,
                        'di_nbcol' : nbcol,
                        'di_nbpal' : nbpal,
                        'di_nbpiece' : nbpiece,
                        'di_poin' : poids,
                        'di_mont' : mont,
                        'di_cmp' : cmp        
                        }
              
            cout_jour.create(data)
            self.env.cr.commit()                        
                                    
    
    def di_generer_couts(self):        
        articles = self.env['product.product'].search([('company_id','=', self.env.user.company_id.id)])
        date_lancement = datetime.today().date()
#         pour tests
#         date_lancement=date_lancement.replace(month=3)
#         date_lancement=date_lancement.replace(day=19)
        
        
        for article in articles:  

            move = self.env['stock.move'].search([ ('product_id', '=', article.id)], limit=1)
            if move:            
                self.di_generer_cmp(article.id, date_lancement)
                #mise à jour du cout de la fiche article ( qui va se renseigner en auto sur les ventes)
                cout = self.env['di.cout'].di_get_cout_uom(article.id,date_lancement)
                data ={'standard_price': cout}                           
                article.write(data)
                
                
                di_cout = self.env['di.cout'].search(['&', ('di_product_id', '=', article.id), ('di_date', '=', date_lancement)])
                
                code_tarif = self.env['di.code.tarif'].search([('name','=','CMP')])
    #             code_tarif = self.env['di.code.tarif'].browse('CMP')
                
                if not code_tarif:
                    data = {
                                'name': 'CMP',
                                'di_des': 'Tarif CMP'                                                                                                                                                
                                } 
                    self.env['di.code.tarif'].create(data)
                    code_tarif = self.env['di.code.tarif'].search([('name','=','CMP')])
                    
                #création tarif uom
                data = {'di_product_id': di_cout.di_product_id.id,
                                'di_code_tarif_id': code_tarif.id,                                                        
                                'di_prix': di_cout.di_cmp,
                                'di_qte_seuil': 0.0,
                                'di_date_effet': di_cout.di_date                                                            
                                }      
                                 
                #recherche si tarif existant                                    
                tarif_existant = self.env["di.tarifs"].search(['&',('di_code_tarif_id', '=', code_tarif.id),
                                                               ('di_date_effet','=',di_cout.di_date),
                                                               ('di_company_id','=',self.env.user.company_id.id),
                                                               ('di_product_id','=',di_cout.di_product_id.id),
                                                               ('di_partner_id','=',False),
                                                               ('di_un_prix','=',False),
                                                               ('di_qte_seuil','=',0.0)
                                                               ])
                        
                if tarif_existant:
                    # si il existe, on le met à jour
                    tarif_existant.update(data)     
                else:
                    #sinon on le créé
                    self.env["di.tarifs"].create(data)
                    
                    
                    
                #création tarif colis
                if article.di_un_prix == 'COLIS' or self.di_generer_tous_tar:
                    if di_cout.di_nbcol !=0.0:
                        cout_un = di_cout.di_mont/di_cout.di_nbcol
                    else:
                        cout_un = di_cout.di_mont
                        
                    data = {'di_product_id': di_cout.di_product_id.id,
                                    'di_code_tarif_id': code_tarif.id,                                                        
                                    'di_prix': cout_un,
                                    'di_qte_seuil': 0.0,
                                    'di_date_effet': di_cout.di_date,
                                    'di_un_prix':'COLIS'                                                            
                                    }      
                                     
                    #recherche si tarif existant                                    
                    tarif_existant = self.env["di.tarifs"].search(['&',('di_code_tarif_id', '=', code_tarif.id),
                                                                   ('di_company_id','=',self.env.user.company_id.id),
                                                                   ('di_product_id','=',di_cout.di_product_id.id),
                                                                   ('di_partner_id','=',False),
                                                                   ('di_un_prix','=','COLIS'),
                                                                   ('di_qte_seuil','=',0.0)
                                                                   ])
                            
                    if tarif_existant:
                        # si il existe, on le met à jour
                        tarif_existant.update(data)     
                    else:
                        #sinon on le créé
                        self.env["di.tarifs"].create(data)
                    
                
                #création tarif piece
                if article.di_un_prix == 'PIECE' or self.di_generer_tous_tar:
                    if di_cout.di_nbpiece !=0.0:
                        cout_un = di_cout.di_mont/di_cout.di_nbpiece
                    else:
                        cout_un = di_cout.di_mont
                        
                    data = {'di_product_id': di_cout.di_product_id.id,
                                    'di_code_tarif_id': code_tarif.id,                                                        
                                    'di_prix': cout_un,
                                    'di_qte_seuil': 0.0,
                                    'di_date_effet': di_cout.di_date,
                                    'di_un_prix':'PIECE'                                                            
                                    }      
                                     
                    #recherche si tarif existant                                    
                    tarif_existant = self.env["di.tarifs"].search(['&',('di_code_tarif_id', '=', code_tarif.id),
                                                                   ('di_date_effet','=',di_cout.di_date),
                                                                   ('di_company_id','=',self.env.user.company_id.id),
                                                                   ('di_product_id','=',di_cout.di_product_id.id),
                                                                   ('di_partner_id','=',False),
                                                                   ('di_un_prix','=','PIECE'),
                                                                   ('di_qte_seuil','=',0.0)
                                                                   ])
                            
                    if tarif_existant:
                        # si il existe, on le met à jour
                        tarif_existant.update(data)     
                    else:
                        #sinon on le créé
                        self.env["di.tarifs"].create(data)
                    
                
                #création tarif palette
                if article.di_un_prix == 'PALETTE' or self.di_generer_tous_tar:
                    if di_cout.di_nbpal !=0.0:
                        cout_un = di_cout.di_mont/di_cout.di_nbpal
                    else:
                        cout_un = di_cout.di_mont
                        
                    data = {'di_product_id': di_cout.di_product_id.id,
                                    'di_code_tarif_id': code_tarif.id,                                                        
                                    'di_prix': cout_un,
                                    'di_qte_seuil': 0.0,
                                    'di_date_effet': di_cout.di_date,
                                    'di_un_prix':'PALETTE'                                                            
                                    }      
                                     
                    #recherche si tarif existant                                    
                    tarif_existant = self.env["di.tarifs"].search(['&',('di_code_tarif_id', '=', code_tarif.id),
                                                                   ('di_date_effet','=',di_cout.di_date),
                                                                   ('di_company_id','=',self.env.user.company_id.id),
                                                                   ('di_product_id','=',di_cout.di_product_id.id),
                                                                   ('di_partner_id','=',False),
                                                                   ('di_un_prix','=','PALETTE'),
                                                                   ('di_qte_seuil','=',0.0)
                                                                   ])
                            
                    if tarif_existant:
                        # si il existe, on le met à jour
                        tarif_existant.update(data)     
                    else:
                        #sinon on le créé
                        self.env["di.tarifs"].create(data)
                        
                #création tarif KG
                if article.di_un_prix == 'KG' or self.di_generer_tous_tar:
                    if di_cout.di_poin !=0.0:
                        cout_un = di_cout.di_mont/di_cout.di_poin
                    else:
                        cout_un = di_cout.di_mont
                        
                    data = {'di_product_id': di_cout.di_product_id.id,
                                    'di_code_tarif_id': code_tarif.id,                                                        
                                    'di_prix': cout_un,
                                    'di_qte_seuil': 0.0,
                                    'di_date_effet': di_cout.di_date,
                                    'di_un_prix':'KG'                                                            
                                    }      
                                     
                    #recherche si tarif existant                                    
                    tarif_existant = self.env["di.tarifs"].search(['&',('di_code_tarif_id', '=', code_tarif.id),
                                                                   ('di_date_effet','=',di_cout.di_date),
                                                                   ('di_company_id','=',self.env.user.company_id.id),
                                                                   ('di_product_id','=',di_cout.di_product_id.id),
                                                                   ('di_partner_id','=',False),
                                                                   ('di_un_prix','=','KG'),
                                                                   ('di_qte_seuil','=',0.0)
                                                                   ])
                            
                    if tarif_existant:
                        # si il existe, on le met à jour
                        tarif_existant.update(data)     
                    else:
                        #sinon on le créé
                        self.env["di.tarifs"].create(data)
                
        #raise Warning("Traitement terminé")  
#         self.afficher_message_fin()
        return self.env['di.popup.wiz'].afficher_message("Traitement terminé.",True,False,False,False) 
#         return {                    
#             'name':'Traitement terminé',            
#             'button_ok':True,
#             'button_yes':False,
#             'button_no':False,
#             'button_cancel':False,
#             'type': 'ir.actions.act_window',
#             'view_type': 'form',
#             'view_mode': 'form',
#             'res_model': 'di.popup.wiz',
#             'target':'new'                    
#             }     
            
        
    @api.model
    def default_get(self, fields):
        res = super(DiGenCoutsWiz, self).default_get(fields)                                     
        return res    