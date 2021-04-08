
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
    di_product_ids = fields.Many2many('product.product')

    def di_generer_cmp(self,di_product_id,di_date, premier_mouv_date=False):
        cout_jour = self.env['di.cout'].search(['&', ('di_product_id', '=', di_product_id.id), ('di_date', '=', di_date)])
        if cout_jour and self.di_supp_cout_jour:
            cout_jour.unlink()
            cout_jour = self.env['di.cout']
        
        if not cout_jour:

            date_veille = di_date + timedelta(days=-1)
            
            if not premier_mouv_date:
                
                query_args = {'product_id': di_product_id.id,'di_date':di_date}               
                query = """ select sp.date_done 
                from stock_move sm
                left join stock_picking sp on sp.id = sm.picking_id
                where sm.product_id = %(product_id)s 
                and sm.state= 'done' 
                and sp.id is not null            
                order by sp.date_done 
                limit 1"""
                self.env.cr.execute(query, query_args)
                                                                                                       
                premier_mouv_done_date = False
                try: 
                    result = self.env.cr.fetchall()[0] 
                    premier_mouv_done_date = result[0] and result[0] or False                
                except:
                    premier_mouv_done_date = False      
                
             
                premier_mouv_date =premier_mouv_done_date    
                
                if self.di_cde_ach: 
                    query_args = {'product_id': di_product_id.id,'di_date':di_date}              
                    query = """ select sp.scheduled_date 
                    from stock_move sm
                    left join stock_picking sp on sp.id = sm.picking_id
                    where sm.product_id = %(product_id)s 
                    and sm.state= 'assigned' 
                    and sp.id is not null            
                    order by sp.scheduled_date 
                    limit 1"""
                    self.env.cr.execute(query, query_args)
                                                                                                           
                    premier_mouv_assigned_date = False
                    try: 
                        result = self.env.cr.fetchall()[0] 
                        premier_mouv_assigned_date = result[0] and result[0] or False                
                    except:
                        premier_mouv_assigned_date = False  
                    
                    if premier_mouv_assigned_date and ( not premier_mouv_date and  premier_mouv_assigned_date < premier_mouv_done_date):
                        premier_mouv_date = premier_mouv_assigned_date

            if premier_mouv_date:
                cout_veille = self.env['di.cout'].search(['&', ('di_product_id', '=', di_product_id.id), ('di_date', '=', date_veille)], limit=1)

                if not cout_veille and ( (self.di_cde_ach and (date_veille >= premier_mouv_date.date()))or(not self.di_cde_ach and (date_veille >= premier_mouv_date.date()))) :
                    self.di_generer_cmp(di_product_id,date_veille,premier_mouv_date)
                    cout_veille = self.env['di.cout'].search(['&', ('di_product_id', '=', di_product_id.id), ('di_date', '=', date_veille)], limit=1)

            
                qte = 0.0
                mont =0.0
                nbcol=0.0
                nbpal=0.0
                nbpiece=0.0
                poids=0.0
                
                dernier_id_cout_veille = 0
                if cout_veille:
                    dernier_id_cout_veille = cout_veille.dernier_id
                    date_cr_cout_veille = cout_veille.write_date#.date()
                else:
                    date_cr_cout_veille = datetime(1900,1,1)#.date()
                    
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

                        cmp=0
                
                if cmp<=0:
                    cmp=cout_veille.di_cmp   
    #     
                if qte==0.0:
                    mont=0.0        
                data ={
                            'di_date': di_date,  
                            'di_product_id' : di_product_id.id,
                            'di_qte' : qte,
                            'di_nbcol' : nbcol,
                            'di_nbpal' : nbpal,
                            'di_nbpiece' : nbpiece,
                            'di_poin' : poids,
                            'di_mont' : mont,
                            'di_cmp' : cmp,
                            'dernier_id':dernier_id        
                            }
                  
                di_cout = self.env['di.cout'].search(['&', ('di_product_id', '=', di_product_id.id), ('di_date', '=', di_date)])
                if not di_cout:
                    cout_jour.create(data)
                    self.env.cr.commit()                        
                                    
    
    def di_generer_couts(self):    
        if self.di_product_ids:
            articles = self.di_product_ids   
            self.di_supp_tous_couts = False     
        elif self.di_product_id:
            articles = self.di_product_id
        else:    
            articles = self.env['product.product'].search([('company_id','=', self.env.user.company_id.id)])
            self.di_supp_tous_couts = False

        date_lancement = self.di_date_gen
        
        for article in articles:  
            if self.di_supp_tous_couts: 
                query_args = {'product_id': self.di_product_id.id}                
                query = """ delete from di_cout where di_product_id = %(product_id)s"""
                self.env.cr.execute(query, query_args)
                self._cr.commit()             
       
            query_args = {'product_id': article.id}                
            query = """ select id from stock_move where product_id = %(product_id)s limit 1 """            
            self.env.cr.execute(query, query_args)                                                 
        
            try: 
                result = self.env.cr.fetchall()[0] 
                move = result[0] and result[0] or False
            except:
                move=False                      

#            move = self.env['stock.move'].search([ ('product_id', '=', article.id)], limit=1)
            if move:            
                self.di_generer_cmp(article, date_lancement,False)
                #mise à jour du cout de la fiche article ( qui va se renseigner en auto sur les ventes)
                cout = self.env['di.cout'].di_get_cout_uom(article.id,date_lancement)
                data ={'standard_price': cout}                           
                article.write(data)
                                
                #di_couts = self.env['di.cout'].search(['&', ('di_product_id', '=', article.id), ('di_date', '=', date_lancement)])
                di_cout = self.env['di.cout'].search(['&', ('di_product_id', '=', article.id), ('di_date', '=', date_lancement)],limit=1)
                if di_cout:
                    #for di_cout in di_couts:
            
                    code_tarif = self.env['di.code.tarif'].search([('name','=','CMP')])
        #             code_tarif = self.env['di.code.tarif'].browse('CMP')
                    
                    if not code_tarif:
                        data = {
                                    'name': 'CMP',
                                    'di_des': 'Tarif CMP'                                                                                                                                                
                                    } 
                        self.env['di.code.tarif'].create(data)
                        code_tarif = self.env['di.code.tarif'].search([('name','=','CMP')])
                                                    
                        
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
                    
                        #break                
        return self.env['di.popup.wiz'].afficher_message("Traitement terminé.",True,False,False,False) 
    
    
    
    def di_generer_couts_cron(self):  
#         self.di_product_ids = self.env['product.product'].search(['&', ('type', '!=', 'service'), '|', '|', ('qty_available', '>', 0.0), ('qty_available', '<', 0.0), ('di_flg_avec_ventes', '=', True)])            
#         articles = self.env['product.product'].search([('company_id','=', self.env.user.company_id.id)])
        date_lancement = self.di_date_gen
        articles = self.env['product.product'].search(['&',('company_id','=', self.env.user.company_id.id),('qty_available', '<=', 0.0)])
        for article in articles:
            dernier_id = 0
            cout_jour = self.env['di.cout'].search(['&', ('di_product_id', '=', article.id), ('di_date', '=', date_lancement)])
            if not cout_jour or cout_jour.di_qte == 0:   
                if cout_jour:   
                    dernier_id  = cout_jour.dernier_id 
                    cout_jour.unlink()
                
                cout_jour = self.env['di.cout']
                            
                cout_veille = self.env['di.cout'].search(['&', ('di_product_id', '=', article.id), ('di_date', '<', date_lancement)], limit=1)
                if not dernier_id : 
                    dernier_id = cout_veille.dernier_id
                
                data ={
                                    'di_date': date_lancement,  
                                    'di_product_id' : article.id,
                                    'di_qte' : 0,
                                    'di_nbcol' : 0,
                                    'di_nbpal' : 0,
                                    'di_nbpiece' : 0,
                                    'di_poin' : 0,
                                    'di_mont' : 0,
                                    'di_cmp' : cout_veille.di_cmp,
                                    'dernier_id':dernier_id  and dernier_id or 0      
                                    }
                                      
                cout_jour.create(data)
                self.env.cr.commit()  
            else:
                
                article.update({'di_cmp_cron_gen':True})
        
        
        articles = self.env['product.product'].search(['&',('company_id','=', self.env.user.company_id.id),('qty_available', '>', 0.0)])
        self.di_supp_tous_couts = False
                             
        if articles:
            articles.update({'di_cmp_cron_gen':True})
            #query = """ UPDATE  product_product set di_cmp_cron_gen  = true""" 
            #self.env.cr.execute(query, )
            self._cr.commit()                                            
            articles.create_cron_gen_cmp(date_lancement,self.di_supp_cout_jour,self.di_generer_tous_tar,self.di_cde_ach)                
            
    def di_regenerer_couts(self):      
        #self.env['product.product'].search([('company_id','=', self.env.user.company_id.id)]).update({'di_cmp_regen':False})        
        query = """ UPDATE  product_product set di_cmp_regen  = false"""
 
        self.env.cr.execute(query, )
        self._cr.commit()
        article = self.env['product.product'].search(['&',('company_id','=', self.env.user.company_id.id),('di_cmp_regen','=', False)],limit=1)
        if article:
            article.create_cron_regen_cmp()        
        
    @api.model
    def default_get(self, fields):
        res = super(DiGenCoutsWiz, self).default_get(fields)                                     
        return res    