# -*- coding: utf-8 -*-


from datetime import datetime

from odoo import api, fields, models


class DiApportProd(models.Model):
    _name = "di.apportprod"
    _description = "Apports producteurs"
    _order = "name"
    
    di_company_id = fields.Many2one('res.company', string='Société', readonly=True,  default=lambda self: self.env.user.company_id)                 
    name = fields.Char(string="Code",compute='_changer_nom',store=True)
    di_product_id = fields.Many2one('product.product', string='Article', required=True)
    di_qte_theo = fields.Float(string="Quantité théorique en unité de référence",required=True,default=0.0)
    di_qte_recept = fields.Float(string="Quantité receptionnée en unité de référence",default=0.0)
    di_exploitation = fields.Char(string="Exploitation d'origine",required=True)
    di_date_estim = fields.Date(string="Date de réception estimée")
    di_date_recept = fields.Date(string="Date de réception")
    di_lot_prod = fields.Char(string="Lot producteur",required=True)
    di_apport_valide = fields.Boolean(string="Validé", default=False)
    di_producteur_id = fields.Many2one("res.partner",string="Producteur")
    di_producteur_nom = fields.Char(related='di_producteur_id.display_name')
    di_station_id = fields.Many2one("stock.location",string="Station")
    di_station_di_des = fields.Char(related='di_station_id.name')
    
    @api.depends('di_station_di_des','di_lot_prod','di_producteur_nom')
    def _changer_nom(self):                 
        self.name=self.di_station_di_des+' - '+self.di_lot_prod+' - '+self.di_producteur_nom
                    
                    
#                     TODO : En cours validation apport avec entrée en stock
#     def valider_apport(self,lot_prod,producteur,station,qte_recue,date_recept):
#          apport = self.search(['&', ('di_lot_prod', '=', lot_prod), ('di_producteur_id', '=', producteur.id), ('di_station_id', '=', station.id)])   
#         if apport :     
#             if not apport.di_apport_valide:
#                 data = { 'di_qte_recept' : qte_recue,
#                         'di_date_recept' : date_recept,
#                         'di_apport_valide' : True
#                     }
#                 
#                 apport.update(data) 
#                 
#                 self.generer_entree_stock(apport)
# 
#             
#     def generer_entree_stock(self,apport):
#         picking = self.env['stock.picking']
#         move = self.env['stock.move']
#         move_line = self.env['stock.move.line']
#         
#         if apport.di_qte_recept:
#             if apport.di_qte_recept > 0.0:
#         
#                 data_picking = { 
#                 'move_type':'direct'
#                 #,
# #                 'state': ,
# #                 'group_id':,
# #                 'priority':'1',
#                         }
#                 data_move = { 
#                         }
#                 data_move_line = { 
#                         }
#                 
#                 picking.create(data_picking)
#                 move.create(data_move)
#                 move_line.create(data_move_line)
#                 
#                 #valider l'entrée en stock
#         

    