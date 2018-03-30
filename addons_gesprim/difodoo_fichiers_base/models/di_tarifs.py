# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
import datetime
    
class DiTarifs(models.Model):
    _name = "di.tarifs"
    _description = "Tarifs"
    _order = "di_date_effet desc"
    
#     name = fields.Char(string="Code", required=True)
    di_company_id = fields.Many2one('res.company', string='Société', readonly=True,  default=lambda self: self.env.user.company_id)             
    di_product_id = fields.Many2one('product.product', string='Article', required=True)    
    di_code_tarif_id = fields.Many2one('di.code.tarif', string='Code tarif', required=True)
    di_partner_id = fields.Many2one('res.partner',string="Client")
    di_un_prix    = fields.Selection([("PIECE", "Pièce"), ("COLIS", "Colis"),("PALETTE", "Palette"),("POIDS","Poids")], string="Unité de prix",required=True)
    di_prix = fields.Float(string="Prix",required=True,default=0.0)
    di_qte_seuil = fields.Float(string="Quantité seuil",required=True,default=0.0)
    di_date_effet = fields.Date(string="Date d'effet", required=True)
    di_date_fin = fields.Date(string="Date de fin")
    
    def _di_get_prix(self, tiers, article, di_un_prix , qte, date):            
        prix=0.0
        # recheche du prix avec un client spécifique
        if date ==False:
#             date=datetime.datetime.now()
            date=fields.Date.today()
        if tiers.di_code_tarif_id.id :
            query_args = {'di_product_id': article.id,'di_code_tarif_id' : tiers.di_code_tarif_id.id,'di_partner_id' : tiers.id,'di_qte_seuil':qte,'di_date':date,'di_un_prix':di_un_prix}
            query = """ SELECT  di_prix 
                            FROM di_tarifs                         
                            WHERE di_product_id = %(di_product_id)s
                            AND di_partner_id = %(di_partner_id)s 
                            AND di_code_tarif_id=%(di_code_tarif_id)s
                            AND di_un_prix=%(di_un_prix)s
                            AND di_qte_seuil<=%(di_qte_seuil)s
                            AND di_date_effet <= %(di_date)s
                            AND 
                            (di_date_fin >= %(di_date)s OR di_date_fin is null)
                            ORDER BY di_date_effet desc,di_qte_seuil desc
                            LIMIT 1
                            """
    
            self.env.cr.execute(query, query_args)
            prix_multi = [(r[0]) for r in self.env.cr.fetchall()]
            #r= self.env.cr.fetchall()
            for prix_simple in prix_multi:
                prix=prix_simple
    #         if r :
    #             prix=r[0]
                    
            # recheche du prix sans client spécifique
            if prix==0.0 :   
                query_args = {'di_product_id': article.id,'di_code_tarif_id' : tiers.di_code_tarif_id.id,'di_qte_seuil':qte,'di_date':date,'di_un_prix':di_un_prix}         
                query = """ SELECT di_prix 
                            FROM di_tarifs                         
                            WHERE di_product_id = %(di_product_id)s                        
                            AND di_code_tarif_id=%(di_code_tarif_id)s
                            AND di_un_prix=%(di_un_prix)s
                            AND di_qte_seuil<=%(di_qte_seuil)s
                            AND di_date_effet <= %(di_date)s
                            
                            AND 
                            (di_date_fin >= %(di_date)s OR di_date_fin is null)
                            ORDER BY di_date_effet desc,di_qte_seuil desc
                            LIMIT 1
                            """
    
                self.env.cr.execute(query, query_args)         
                prix_multi = [(r[0]) for r in self.env.cr.fetchall()]
                #r= self.env.cr.fetchall()
                for prix_simple in prix_multi:
                    prix=prix_simple   
    #             r2 = self.env.cr.fetchall()
    #             if r2:
    #                 prix = r2[0]
#           
               
        return prix