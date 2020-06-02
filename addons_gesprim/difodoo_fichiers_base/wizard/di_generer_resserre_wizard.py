
# -*- coding: utf-8 -*-

from odoo import api, fields, models
from datetime import date, timedelta, datetime
from odoo.exceptions import ValidationError
from odoo.exceptions import Warning


class DiGenResserreWiz(models.TransientModel):
    _name = "di.gen.resserre.wiz"
    _description = "Wizard de génération de resserre"
        
    di_date_gen = fields.Datetime('Date de génération', default=datetime.today() )
    
    def di_generer_resserre_art(self,id,date):
        
        query_args = {'product_id': id,'date':date}    
                       
        query = """ select id  from di_resserre where product_id = %(product_id)s and date < %(date)s order by date desc  limit 1 """            
        self.env.cr.execute(query, query_args)                                                 
    
        try: 
            result = self.env.cr.fetchall()[0] 
            id_dern_ress = result[0] and result[0] or False
        except:
            id_dern_ress=False   
        if id_dern_ress :    
            dern_ress = self.env['di.resserre'].browse(id_dern_ress)
        else:
            dern_ress=False
            
        if dern_ress:
            date_deb= dern_ress.date
        else:
            date_deb= datetime(2000, 1, 1)
            
        if date_deb.date() != date.date():
                    
            sqlstr = """
                                select
                                    SUM ( Case when sml.di_usage_loc_dest = 'internal' then sml.di_nb_colis else -1*sml.di_nb_colis end) AS di_col_stock,
                                    SUM ( Case when sml.di_usage_loc_dest = 'internal' then sml.qty_done else -1*sml.qty_done end) AS di_qte_stock,
                                    SUM ( Case when sml.di_usage_loc_dest = 'internal' then sml.di_poib else -1*sml.di_poib end) AS di_poib_stock,
                                    SUM ( Case when sml.di_usage_loc_dest = 'internal' then sml.di_poin else -1*sml.di_poin end) AS di_poin_stock,                                
                                    SUM ( Case when sml.di_usage_loc_dest = 'internal' then cmp.di_cmp*sml.qty_done else -1*cmp.di_cmp*sml.qty_done end) AS di_val_stock                                                                                        
                                from stock_move_line sml                                
                                LEFT JOIN (select di_cout.di_cmp,di_cout.id,di_cout.di_product_id from di_cout ) cmp on cmp.id = 
                                (select id from di_cout where di_product_id = sml.product_id order by di_date desc limit 1)                                         
                                LEFT JOIN stock_production_lot lot on lot.id = sml.lot_id            
                                where sml.product_id = %s and sml.state ='done'  and sml.date <=%s and lot.di_fini is false and sml.date > %s
                                
                                """
                 
            self.env.cr.execute(sqlstr, (id, date, date_deb))
            result = self.env.cr.fetchall()[0]
            di_col_stock = result[0] and result[0] or 0.0
            di_qte_stock = result[1] and result[1] or 0.0
            di_poib_stock = result[2] and result[2] or 0.0
            di_poin_stock = result[3] and result[3] or 0.0
            di_val_stock = result[4] and result[4] or 0.0
              
            
            if  dern_ress:
                di_col_stock = dern_ress.di_col_stock +di_col_stock
                di_qte_stock = dern_ress.di_qte_stock+di_qte_stock
                di_poib_stock = dern_ress.di_poib_stock+di_poib_stock
                di_poin_stock = dern_ress.di_poin_stock+di_poin_stock
                di_val_stock = dern_ress.di_val_stock+di_val_stock
                
                
                
            sqlstr = """
                                select                                                                
                                    SUM ( Case when sml.di_usage_loc = 'internal' and  sml.di_usage_loc_dest = 'customer' then sml.di_nb_colis when sml.di_usage_loc = 'customer' and sml.di_usage_loc_dest = 'internal' then -1*sml.di_nb_colis  else   0 end) AS di_col_ven,
                                    
                                    SUM ( Case when sml.di_usage_loc = 'internal' and  sml.di_usage_loc_dest = 'customer' then sml.qty_done when sml.di_usage_loc = 'customer' and sml.di_usage_loc_dest = 'internal' then -1*sml.qty_done else 0 end) AS di_qte_ven,
                                    SUM ( Case when sml.di_usage_loc = 'internal' and  sml.di_usage_loc_dest = 'customer' then sml.di_poib when sml.di_usage_loc = 'customer' and sml.di_usage_loc_dest = 'internal' then -1* sml.di_poib else 0 end) AS di_poib_ven,
                                    SUM ( Case when sml.di_usage_loc = 'internal' and  sml.di_usage_loc_dest = 'customer' then sml.di_poin when sml.di_usage_loc = 'customer' and sml.di_usage_loc_dest = 'internal' then -1*sml.di_poin else 0 end) AS di_poin_ven,
                                    
                                    SUM ( Case when sml.di_usage_loc = 'internal' and  sml.di_usage_loc_dest = 'customer' then sml.qty_done*sol.price_unit when sml.di_usage_loc = 'customer' and sml.di_usage_loc_dest = 'internal' then -1*sml.qty_done*sol.price_unit else 0 end) AS di_val_ven                                                                                                                                            
                                    
                                from stock_move_line sml                                                                          
                                LEFT JOIN (select sm.sale_line_id, sm.id  from stock_move sm) sm on sm.id = sml.move_id  
                                LEFT JOIN (select sol.price_unit, sol.id from sale_order_line sol) sol on sol.id = sm.sale_line_id     
                                LEFT JOIN stock_production_lot lot on lot.id = sml.lot_id            
                                where sml.product_id = %s and sml.state ='done'  and sml.date <=%s and lot.di_fini is false  and sml.di_flg_cloture is not true and (sml.di_usage_loc = 'customer' or sml.di_usage_loc_dest = 'customer' ) 
                                
                                """             
            self.env.cr.execute(sqlstr, (id, date))
            result = self.env.cr.fetchall()[0]
            di_col_ven = result[0] and result[0] or 0.0
            di_qte_ven = result[1] and result[1] or 0.0
            di_poib_ven = result[2] and result[2] or 0.0
            di_poin_ven = result[3] and result[3] or 0.0
            di_val_ven = result[4] and result[4] or 0.0
            
            
            
            sqlstr = """
                                select                                                                
                                
                                    SUM ( sml.di_nb_colis ) AS di_col_regul_sortie,
                                    SUM ( sml.qty_done) AS di_qte_regul_sortie,
                                    SUM ( sml.di_poib) AS di_poib_reg_sort,
                                    SUM ( sml.di_poin) AS di_poin_reg_sort                                  
                                                                      
                                from stock_move_line sml                                                                          
                                LEFT JOIN (select sm.sale_line_id, sm.id  from stock_move sm) sm on sm.id = sml.move_id  
                                LEFT JOIN (select sol.price_unit, sol.id from sale_order_line sol) sol on sol.id = sm.sale_line_id     
                                LEFT JOIN stock_production_lot lot on lot.id = sml.lot_id            
                                where sml.product_id = %s and sml.state ='done'  and sml.date <=%s and lot.di_fini is false  and sml.di_flg_cloture is not true and sml.di_usage_loc = 'internal' and  sml.di_usage_loc_dest <> 'customer' and sml.di_perte is true 
                                
                                """             
            self.env.cr.execute(sqlstr, (id, date))
            result = self.env.cr.fetchall()[0]
            
            di_col_regul_sortie = result[0] and result[0] or 0.0
            di_qte_regul_sortie = result[1] and result[1] or 0.0
            di_poib_reg_sort = result[2] and result[2] or 0.0
            di_poin_reg_sort = result[3] and result[3] or 0.0
                      
            product = self.env['product.product'].browse(id)                    
            if di_qte_stock != 0.0:
                di_prix_achat_moyen = di_val_stock / di_qte_stock
            else:
                di_prix_achat_moyen = product.product_tmpl_id.standard_price
                
            di_val_marge = di_val_ven - (di_qte_ven*di_prix_achat_moyen)
                
            if di_qte_ven != 0.0:
                di_prix_vente_moyen = di_val_ven / di_qte_ven
            else:
                di_prix_vente_moyen =0.0
                
            if di_val_ven != 0.0:    
                di_marge_prc = di_val_marge * 100 / di_val_ven
            else:
                di_marge_prc = 0.0
                
            di_val_regul_sortie =  di_prix_achat_moyen *  di_qte_regul_sortie
            di_val_marge_ap_regul_sortie =  di_val_marge -  di_val_regul_sortie 
            
            
            data ={
                                'product_id': id,  
                                'uom_id' : product.uom_id.id,
                                'date' : date,
                                'di_prix_vente_moyen' : di_prix_vente_moyen,
                                'di_prix_achat_moyen' : di_prix_achat_moyen,
                                'di_val_ven' : di_val_ven,
                                'di_val_stock' : di_val_stock,
                                'di_val_marge' : di_val_marge,
                                'di_marge_prc' : di_marge_prc,
                                'di_col_stock':di_col_stock,
                                'di_qte_stock':di_qte_stock,
                                'di_poib_stock':di_poib_stock,
                                'di_poin_stock':di_poin_stock,
                                'di_col_ven':di_col_ven,
                                'di_qte_ven':di_qte_ven,
                                'di_poib_ven':di_poib_ven,
                                'di_poin_ven':di_poin_ven,
                                'di_col_regul_sortie':di_col_regul_sortie,
                                'di_qte_regul_sortie':di_qte_regul_sortie,
                                'di_poib_reg_sort':di_poib_reg_sort,
                                'di_poin_reg_sort':di_poin_reg_sort,
                                'di_val_regul_sortie':di_val_regul_sortie,
                                'di_val_marge_ap_regul_sortie':di_val_marge_ap_regul_sortie,                            
                                        
                                }                            
            self.env['di.resserre'].create(data)
            self.env.cr.commit()
        

    def di_generer_resserre(self):  
        
        query = """ UPDATE  product_product set di_ress_regen  = false""" 
        self.env.cr.execute(query, )
        self._cr.commit()
                
        query = """ SELECT  pp.id 
                        FROM product_product pp  
                        left join product_template pt on pt.id = pp.product_tmpl_id                      
                        WHERE pt.type <> 'service' 
                        and (
                        di_flg_avec_ventes is true
                        or (select sum(sq.quantity) from stock_quant sq left join stock_location sl on sl.id = sq.location_id where sq.product_id = pp.id and sl.usage='internal' ) not between -0.001 and 0.001
                        ) and pp.di_ress_regen = false      
                        limit 50                                                                                    
                        """
 
        self.env.cr.execute(query, )
        ids = [r[0] for r in self.env.cr.fetchall()]
                                     
        date_lancement = self.di_date_gen+timedelta(hours=+2)
        
        products = self.env['product.product'].browse(ids)
        if products:
            products.create_cron_regen_resserre(date_lancement) 
        
#         for id in ids:                                                          
#             self.di_generer_resserre_art(id, date_lancement)
                               
        return self.env['di.popup.wiz'].afficher_message("Génération lancée en arrière plan. Veuillez patienter.",True,False,False,False) 
            
        
    @api.model
    def default_get(self, fields):
        res = super(DiGenResserreWiz, self).default_get(fields)                                     
        return res    