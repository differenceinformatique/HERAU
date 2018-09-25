
# -*- coding: utf-8 -*-

from odoo import api, fields, models
from datetime import date, timedelta, datetime
from odoo.exceptions import ValidationError


class DiConsLineWiz(models.TransientModel):
    _name = "di.cons.line.wiz"
    _description = "Wizard de génération des lignes de consignes chez le client."
    
    di_lot_id = fields.Many2one("stock.production.lot",string="Lot")
    di_lot_name = fields.Char(related='di_lot_id.name',store=True)
    di_product_id =  fields.Many2one("product.product",string="Article")   
    di_product_name = fields.Char(related='di_product_id.name',store=True)
    di_parter_id = fields.Many2one("res.partner",string="Client")
    di_partner_name = fields.Char(related='di_parter_id.name',store=True) 
    di_select  = fields.Boolean(string="Sélection", default=False)  
    di_sml_id = fields.Many2one("stock.move.line",string="Id ligne de stock")    
        
    
#     
# #    TODO : Faire un autre wizard qui va être composé de product_id + name, lot_id+name, partner_id+name, case à cocher "sélection" 
# #    Ce wizard sera une liste de l'autre wizard
#     @api.model
#     def default_get(self, fields):
#         self.delete_all()
#         res = super(DiConsLineWiz, self).default_get(fields)         
#         sml_ids = self.env['stock.move.line'].search(['&', ('product_id.di_cons', '=', True), ('state', '=', 'done'), ('lot_id', '!=', False), ('lot_id.di_plus_suivi', '=', False), ('picking_id', '!=', False), ('picking_id.picking_type_id.code', '=', 'outgoing')])         
#                 
#         for sml in sml_ids:   
#             (nbcol,nbpal,nbpiece,poids,qte_std) = self.env['stock.move.line'].di_qte_spe_en_stock(sml.product_id,False,sml.lot_id)
#             if qte_std <=0.0:        
#                 self.create({
#                     'di_lot_id' :sml.lot_id.id, 
#                     'di_product_id'  :sml.product_id.id,
#                     'di_lot_name':sml.lot_id.name,
#                     'di_product_name':sml.product_id.product_tmpl_id.name,
#                     'di_parter_id':sml.picking_id.partner_id.id,
#                     'di_partner_name':sml.picking_id.partner_id.name,
#                     'di_select':False,    
#                     })            
#                         
#         return res    