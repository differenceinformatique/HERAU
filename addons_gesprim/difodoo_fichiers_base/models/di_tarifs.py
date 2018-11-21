
# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from datetime import datetime
from mock.mock import self
    
class DiTarifs(models.Model):
    _name = "di.tarifs"
    _description = "Tarifs"
    _order = "di_date_effet desc"
    
    name = fields.Char(string="Code",compute='_changer_nom',store=True)
    di_company_id = fields.Many2one('res.company', string='Société', readonly=True,  default=lambda self: self.env.user.company_id)             
    di_product_id = fields.Many2one('product.product', string='Article', required=True)        
    di_product_tmpl_id =fields.Many2one(related='di_product_id.product_tmpl_id')#, store='False')
    di_code_tarif_id = fields.Many2one('di.code.tarif', string='Code tarif', required=True)
    di_partner_id = fields.Many2one('res.partner',string="Client")
    di_un_prix    = fields.Selection([("PIECE", "Pièce"), ("COLIS", "Colis"),("PALETTE", "Palette"),("KG","Kg")], string="Unité de prix")
    di_prix = fields.Float(string="Prix",required=True,default=0.0)
    di_qte_seuil = fields.Float(string="Quantité seuil",required=True,default=0.0)
    di_date_effet = fields.Date(string="Date d'effet", required=True)
    di_date_fin = fields.Date(string="Date de fin")
    di_type_palette_id     = fields.Many2one('product.packaging', string='Palette', copy=False)   
    di_type_colis_id       = fields.Many2one('product.packaging', string='Colis', copy=False)
        
    @api.onchange('di_product_id','di_un_prix','di_partner_id')
    def _changer_type_colpal(self):
        if self.di_un_prix=="COLIS":
            self.di_type_palette_id=False
            refart=self.env['di.ref.art.tiers']
            if self.di_partner_id:
                refart=refart.search(['&', ('di_product_id', '=', self.di_product_id), ('di_partner_id', '=', self.di_partner_id)], limit=1)
            if refart.id:
                self.di_type_colis_id=refart.di_type_colis_id
            else:
                self.di_type_colis_id=self.di_product_id.di_type_colis_id
        if self.di_un_prix=="PALETTE":
            self.di_type_palette_id=False
            refart=self.env['di.ref.art.tiers']
            if self.di_partner_id:
                refart=refart.search(['&', ('di_product_id', '=', self.di_product_id), ('di_partner_id', '=', self.di_partner_id)], limit=1)
            if refart.id:
                self.di_type_palette_id=refart.di_type_palette_id
            else:
                self.di_type_palette_id=self.di_product_id.di_type_palette_id
        

    @api.depends('di_company_id','di_product_id','di_code_tarif_id','di_partner_id','di_un_prix','di_qte_seuil','di_date_effet')
    def _changer_nom(self):    
        for tar in self:  
            if tar.di_un_prix:  
                tar.name=tar.di_product_id.default_code+' - '+tar.di_code_tarif_id.name+' - '+tar.di_un_prix +' - '+str(tar.di_qte_seuil)+' - '+ tar.di_date_effet.strftime('%d/%m/%Y')#+' - '+str(self.di_partner_id.ref)
            else:
                tar.name=tar.di_product_id.default_code+' - '+tar.di_code_tarif_id.name+' - '+str(tar.di_qte_seuil)+' - '+ tar.di_date_effet.strftime('%d/%m/%Y')#+' - '+str(self.di_partner_id.ref)
                
    def _di_get_prix(self, tiers, article, di_un_prix , qte, date, typecol, typepal):            
        prix=0.0
        # recheche du prix avec un client spécifique
        
        if di_un_prix =="COLIS":
            idcol=typecol.id                
            idpal=0      
        elif di_un_prix=="PALETTE":
            idpal=typepal.id            
            idcol=0
        else:
            idpal=0
            idcol=0
        if date ==False:
#             date=datetime.datetime.now()
            date=fields.Date.today()
        if tiers.di_code_tarif_id.id :
            query_args = {'di_product_id': article.id,
                          'di_code_tarif_id' : tiers.di_code_tarif_id.id,
                          'di_partner_id' : tiers.id,
                          'di_qte_seuil':qte,
                          'di_date':date,
                          'di_un_prix':di_un_prix, 
                          'di_type_colis_id':idcol,
                          'di_type_palette_id':idpal}            
            
            query = """ SELECT  di_prix 
                            FROM di_tarifs                         
                            WHERE di_product_id = %(di_product_id)s
                            AND di_partner_id = %(di_partner_id)s 
                            AND di_code_tarif_id=%(di_code_tarif_id)s
                            AND di_un_prix=%(di_un_prix)s
                            AND ( case when %(di_type_colis_id)s = 0 then di_type_colis_id is null else di_type_colis_id=%(di_type_colis_id)s end)
                            AND ( case when %(di_type_palette_id)s = 0 then di_type_palette_id is null else di_type_palette_id=%(di_type_palette_id)s end)
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
                query_args = {'di_product_id': article.id,
                              'di_code_tarif_id' : tiers.di_code_tarif_id.id,
                              'di_qte_seuil':qte,
                              'di_date':date,
                              'di_un_prix':di_un_prix,
                              'di_type_colis_id':idcol,
                              'di_type_palette_id':idpal}         
                query = """ SELECT di_prix 
                            FROM di_tarifs                         
                            WHERE di_product_id = %(di_product_id)s                        
                            AND di_code_tarif_id=%(di_code_tarif_id)s
                            AND di_un_prix=%(di_un_prix)s
                            AND ( case when %(di_type_colis_id)s = 0 then di_type_colis_id is null else di_type_colis_id=%(di_type_colis_id)s end)
                            AND ( case when %(di_type_palette_id)s = 0 then di_type_palette_id is null else di_type_palette_id=%(di_type_palette_id)s end)
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
        return prix
    
    
    def di_get_liste_articles(self,date):            
        
       
        query_args = {'di_date':date}
        query = """ SELECT  distinct di_product_id 
                        FROM di_tarifs                         
                        WHERE di_date_effet <= %(di_date)s
                        AND 
                        (di_date_fin >= %(di_date)s OR di_date_fin is null)
                        ORDER BY di_product_id asc                            
                        """

        self.env.cr.execute(query, query_args)
        article_ids = [(r[0]) for r in self.env.cr.fetchall()]
        articles = []
        for article_id in article_ids:
            article=self.env['product.product'].browse(article_id)
            articles.append(article)                        
               
        return articles
    
    def di_get_liste_codes_tarif(self,date):            
        
       
        query_args = {'di_date':date}
        query = """ SELECT distinct di_code_tarif_id 
                        FROM di_tarifs                         
                        WHERE di_date_effet <= %(di_date)s
                        AND 
                        (di_date_fin >= %(di_date)s OR di_date_fin is null)
                        ORDER BY di_code_tarif_id asc                            
                        """

        self.env.cr.execute(query, query_args)
        code_tarifs_ids = [(r[0]) for r in self.env.cr.fetchall()]
        
        codes_tarifs = []
        for code_tarif_id in code_tarifs_ids:
            code_tarif=self.env['di.code.tarif'].browse(code_tarif_id)
            codes_tarifs.append(code_tarif)                        
               
        return codes_tarifs         