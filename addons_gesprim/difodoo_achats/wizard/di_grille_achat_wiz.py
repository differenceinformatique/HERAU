# -*- coding: utf-8 -*-
from odoo import api, fields, models
from datetime import date, timedelta, datetime
from odoo.exceptions import ValidationError

class DiGrilleAchatWiz(models.TransientModel):
    _name = "di.grille.achat.wiz"
    _description = "Wizard d'aide à la saisie de commande de achat"
    
    di_order_id = fields.Many2one("purchase.order", string="Commande", required=True)        
    di_product_ids = fields.Many2many("product.product", string="Dernièrs achats")
    
    @api.multi
    def di_valider_grille(self):
        for product in self.di_product_ids:
            vals = {
                        'order_id': self.di_order_id.id,
                        'date_planned': self.di_order_id.date_planned,
                        'product_id': product.id,
                        'product_uom':product.product_tmpl_id.uom_id.id,
                        'name':product.name,
                        'di_un_saisie': product.di_un_saisie, 
                        'di_type_palette_id': product.di_type_palette_id.id, 
                        'product_packaging': product.di_type_colis_id.id, 
                        'di_un_prix': product.di_un_prix, 
                        'di_spe_saisissable': product.di_spe_saisissable,
                        'product_qty': 0.0, 
                        'price_unit':0.0  
                                                               
                         }          

            self.di_order_id.order_line.create(vals)

    @api.model
    def default_get(self, fields):
        res = super(DiGrilleAchatWiz, self).default_get(fields) 
        param = self.env['di.param'].search([('di_company_id','=',self.env.user.company_id.id)])
        
        date_debut_horizon = datetime.today() + timedelta(days=-param.di_horizon_ach)
        order = self.env['purchase.order'].browse(self.env.context.get('active_id')) # la commande est sauvegardée quand on clique sur le bouton grille de vente
        
        partner_id = order.partner_id
        res['di_order_id']=order.id
                
        lines= self.env['purchase.order.line'].search(['&',('company_id','=',self.env.user.company_id.id),('order_id.partner_id','=',partner_id.id)]).filtered(lambda l: datetime.strptime(l.order_id.date_order,'%Y-%m-%d %H:%M:%S')>=date_debut_horizon)
        liste_articles_ids=[]
        for line in lines:
            liste_articles_ids.append(line.product_id.id)            
        
        res['di_product_ids']=list(set(liste_articles_ids)) # set permet de ne prendre que les valeurs uniques, et list pour reformater en liste
                                                    
        return res    