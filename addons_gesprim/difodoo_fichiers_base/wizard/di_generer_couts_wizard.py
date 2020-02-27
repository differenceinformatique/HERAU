
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
    di_date_gen = fields.Date('Date de génération', default=datetime.today().date() )
    di_product_id = fields.Many2one('product.product',string="Article", help="""Permet de faire la génération sur un article. Laisser vide pour faire tous les articles.""")
    di_supp_cout_jour = fields.Boolean("Supprimer les coûts du jour", default=False)
    di_supp_tous_couts = fields.Boolean("Supprimer tous les coûts de l'article", default=False)

    def di_generer_cmp(self,di_product_id,di_date):
#         if di_date.strftime("%d/%m/%y") == '06/06/19':
#             di_date
        cout_jour = self.env['di.cout'].search(['&', ('di_product_id', '=', di_product_id), ('di_date', '=', di_date)])
        if cout_jour and self.di_supp_cout_jour:
            cout_jour.unlink()
            cout_jour = self.env['di.cout']
        
        if not cout_jour:
            premier_mouv_assigned = False
            premier_mouv_done = False

            date_veille = di_date + timedelta(days=-1)
            mouvs = self.env['stock.move'].search([('product_id','=',di_product_id),('picking_id','!=',False),('state','=','done')]).sorted(key=lambda m: m.picking_id.date_done)
      
            for premier_mouv_done in mouvs:
                break
            
            mouvs = self.env['stock.move'].search([('product_id','=',di_product_id),('picking_id','!=',False),('state','=','assigned')]).sorted(key=lambda m: m.picking_id.scheduled_date)
            premier_mouv = False
            for premier_mouv_assigned in mouvs:
                break
            if premier_mouv_done:
                premier_mouv = premier_mouv_done            
                
            
            if self.di_cde_ach: 
                if premier_mouv_assigned:                                   
                    if  not premier_mouv or  premier_mouv_assigned.picking_id.scheduled_date < premier_mouv.picking_id.date_done:
                        premier_mouv = premier_mouv_assigned


            if premier_mouv:                  
                cout_veille = self.env['di.cout'].search(['&', ('di_product_id', '=', di_product_id), ('di_date', '=', date_veille)])

                if not cout_veille and ( (self.di_cde_ach and (premier_mouv.picking_id.scheduled_date and  date_veille >= premier_mouv.picking_id.scheduled_date.date()))or(not self.di_cde_ach and (premier_mouv.picking_id.date_done and  date_veille >= premier_mouv.picking_id.date_done.date()))) :
                    self.di_generer_cmp(di_product_id,date_veille)
                    cout_veille = self.env['di.cout'].search(['&', ('di_product_id', '=', di_product_id), ('di_date', '=', date_veille)])                  
            
#    Morvan 27/02/202 - je rétablis le précédent programme, car plantage
#             if premier_mouv:
# #                 cout_veille = self.env['di.cout'].search(['&', ('di_product_id', '=', di_product_id), ('di_date', '=', date_veille)])                  
#                 couts_veille = self.env['di.cout'].search(['&', ('di_product_id', '=', di_product_id), ('di_date', '=', date_veille)])
#                 if couts_veille:
#                     for cout_veille in couts_veille:
#                         break
#                       
#                 if not couts_veille and ( (self.di_cde_ach and (premier_mouv.picking_id.scheduled_date and  date_veille >= premier_mouv.picking_id.scheduled_date.date()))or(not self.di_cde_ach and (premier_mouv.picking_id.date_done and  date_veille >= premier_mouv.picking_id.date_done.date()))) :
#                     self.di_generer_cmp(di_product_id,date_veille)
# #                     cout_veille = self.env['di.cout'].search(['&', ('di_product_id', '=', di_product_id), ('di_date', '=', date_veille)])
#                     couts_veille = self.env['di.cout'].search(['&', ('di_product_id', '=', di_product_id), ('di_date', '=', date_veille)])
#                     if couts_veille:
#                         for cout_veille in couts_veille:
#                             break


                
                qte = 0.0
                mont =0.0
                nbcol=0.0
                nbpal=0.0
                nbpiece=0.0
                poids=0.0
                
                dernier_id_cout_veille = 0
                if cout_veille:
                    dernier_id_cout_veille = cout_veille.dernier_id
                    date_cr_cout_veille = cout_veille.write_date.date()
                else:
                    date_cr_cout_veille = datetime(1900,1,1).date()
                dernier_id = 0    
                (qte,mont,nbcol,nbpal,nbpiece,poids,dernier_id,nouveau_cmp) = self.env['stock.move'].di_somme_quantites_montants(di_product_id,date_cr_cout_veille,di_date,self.di_cde_ach,dernier_id_cout_veille)
                qte=round(qte,3)
                mont=round(mont,3)
                nbcol=round(nbcol,3)
                nbpal=round(nbpal,3)
                nbpiece=round(nbpiece,3)
                poids=round(poids,3)
                nouveau_cmp=round(nouveau_cmp,3)
                
                
                if dernier_id == 0:
                    dernier_id=dernier_id_cout_veille
                qte = cout_veille.di_qte + qte
                mont = cout_veille.di_mont+ mont
                nbcol = cout_veille.di_nbcol + nbcol
                nbpal = cout_veille.di_nbpal + nbpal
                nbpiece = cout_veille.di_nbpiece + nbpiece
                poids = cout_veille.di_poin + poids             
                if qte !=0.0 and qte != -0.0:                
                    cmp=round(mont/qte,2)
                else:
                    if nouveau_cmp!=0.0:
                        cmp = nouveau_cmp
                    else:
                        
#                     nbcol = 0
#                     nbpal = 0
#                     nbpiece = 0
#                     poids = 0
#                     mont = 0
#                     cmp=mont
                        cmp=0
                
                if cmp<=0:
                    cmp=cout_veille.di_cmp   
    #     
                if qte==0.0:
                    mont=0.0        
                data ={
                            'di_date': di_date,  
                            'di_product_id' : di_product_id,
                            'di_qte' : qte,
                            'di_nbcol' : nbcol,
                            'di_nbpal' : nbpal,
                            'di_nbpiece' : nbpiece,
                            'di_poin' : poids,
                            'di_mont' : mont,
                            'di_cmp' : cmp,
                            'dernier_id':dernier_id        
                            }
                  
                di_cout = self.env['di.cout'].search(['&', ('di_product_id', '=', di_product_id), ('di_date', '=', di_date)])
                if not di_cout:
#                     if not cout_jour:
#                         cout_jour=self.env['di.cout']
                    cout_jour.create(data)
                    self.env.cr.commit()                        
                                    
    
    def di_generer_couts(self):      
        if self.di_product_id:
            articles = self.di_product_id
        else:    
            articles = self.env['product.product'].search([('company_id','=', self.env.user.company_id.id)])
            self.di_supp_tous_couts = False

#         articles = self.env['product.product'].browse(6817) #T300F              
#         date_lancement = datetime.today().date()#+ timedelta(days=-7)
        
        date_lancement = self.di_date_gen
#         pour tests
#         date_lancement=date_lancement.replace(month=3)
#         date_lancement=date_lancement.replace(day=19)
        
        
        for article in articles:  
            if self.di_supp_tous_couts:                
                couts_art = self.env['di.cout'].search([('di_product_id', '=', self.di_product_id.id)])       
                couts_art.unlink()
       
                
            move = self.env['stock.move'].search([ ('product_id', '=', article.id)], limit=1)
            if move:            
                self.di_generer_cmp(article.id, date_lancement)
                #mise à jour du cout de la fiche article ( qui va se renseigner en auto sur les ventes)
                cout = self.env['di.cout'].di_get_cout_uom(article.id,date_lancement)
                data ={'standard_price': cout}                           
                article.write(data)
                
                
                di_couts = self.env['di.cout'].search(['&', ('di_product_id', '=', article.id), ('di_date', '=', date_lancement)])
                if di_couts:
                    for di_cout in di_couts:
                
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
        #                 data = {'di_product_id': di_cout.di_product_id.id,
        #                                 'di_code_tarif_id': code_tarif.id,                                                        
        #                                 'di_prix': di_cout.di_cmp,
        #                                 'di_qte_seuil': 0.0,
        #                                 'di_date_effet': di_cout.di_date                                                            
        #                                 }      
        #                                  
        #                 #recherche si tarif existant                                    
        #                 tarif_existant = self.env["di.tarifs"].search(['&',('di_code_tarif_id', '=', code_tarif.id),
        #                                                                ('di_date_effet','=',di_cout.di_date),
        #                                                                ('di_company_id','=',self.env.user.company_id.id),
        #                                                                ('di_product_id','=',di_cout.di_product_id.id),
        #                                                                ('di_partner_id','=',False),
        #                                                                ('di_un_prix','=',False),
        #                                                                ('di_qte_seuil','=',0.0)
        #                                                                ])
        #                         
        #                 if tarif_existant:
        #                     # si il existe, on le met à jour
        #                     tarif_existant.update(data)     
        #                 else:
        #                     #sinon on le créé
        #                     self.env["di.tarifs"].create(data)
                            
                            
                            
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
                                            'di_un_prix':'COLIS',
                                            'di_type_colis_id': di_cout.di_product_id.di_type_colis_id.id                                                           
                                            }      
                                             
                            #recherche si tarif existant                                    
                            tarif_existant = self.env["di.tarifs"].search(['&',('di_code_tarif_id', '=', code_tarif.id),
                                                                           ('di_company_id','=',self.env.user.company_id.id),
                                                                           ('di_product_id','=',di_cout.di_product_id.id),
                                                                           ('di_partner_id','=',False),
                                                                           ('di_un_prix','=','COLIS'),
                                                                           ('di_qte_seuil','=',0.0),
                                                                           ('di_type_colis_id','=',di_cout.di_product_id.di_type_colis_id.id)
                                                                           
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
                                            'di_un_prix':'PALETTE',
                                            'di_type_palette_id': di_cout.di_product_id.di_type_palette_id.id                                                            
                                            }      
                                             
                            #recherche si tarif existant                                    
                            tarif_existant = self.env["di.tarifs"].search(['&',('di_code_tarif_id', '=', code_tarif.id),
                                                                           ('di_date_effet','=',di_cout.di_date),
                                                                           ('di_company_id','=',self.env.user.company_id.id),
                                                                           ('di_product_id','=',di_cout.di_product_id.id),
                                                                           ('di_partner_id','=',False),
                                                                           ('di_un_prix','=','PALETTE'),
                                                                           ('di_qte_seuil','=',0.0),
                                                                           ('di_type_palette_id','=',di_cout.di_product_id.di_type_palette_id.id)
                                                                           
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
                        
                        break                
        return self.env['di.popup.wiz'].afficher_message("Traitement terminé.",True,False,False,False) 

        
    @api.model
    def default_get(self, fields):
        res = super(DiGenCoutsWiz, self).default_get(fields)                                     
        return res    