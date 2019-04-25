
# -*- coding: utf-8 -*-

from odoo import api, fields, models
from datetime import date, timedelta, datetime
from odoo.exceptions import ValidationError
from odoo.exceptions import Warning


class DiLivrDirecteWiz(models.TransientModel):
    _name = "di.livr.directe.wiz"
    _description = "Wizard de livraison directe des devis"
     
    di_orders = fields.Many2many("sale.order")
    
    @api.multi
    def di_livraison_directe_masse(self):
        ok = True
        orders_to_deliver = self.di_orders.filtered(lambda o: o.state == 'draft')
        orders_to_deliver.di_action_livrer()   
        for order in orders_to_deliver:
            livraisons = order.mapped('picking_ids')
            for livraison in livraisons:                                  
                if livraison.state!='done':
                    ok = False                    
                    break     
#                 else:
#                     moves = livraison.mapped('move_lines')
#                     for move in moves:
#                         if move.state != 'done':
#                             ok=False
#                             break
        if not ok:
            return self.env['di.popup.wiz'].afficher_message("Attention ! Certaines livraisons n'ont pas pu être validées par manque de stock.",True,False,False,False)    
        else:
            return self.env['di.popup.wiz'].afficher_message("Traitement terminé.",True,False,False,False)  
                                                           
            
    @api.model
    def default_get(self, fields):
        res = super(DiLivrDirecteWiz, self).default_get(fields)                 
        res["di_orders"] = self.env.context["active_ids"]                                                                                                                             
        return res    