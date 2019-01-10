# -*- coding: utf-8 -*-
from odoo import api, fields, models
from datetime import date, timedelta, datetime
from odoo.exceptions import ValidationError

class DiSuppLigZeroWiz(models.TransientModel):
    _name = "di.supp.lig.zero.wiz"
    _description = "Wizard d'aide à la saisie de commande de vente"
    
    di_order_id = fields.Many2one("sale.order", string="Commande")        
    di_line_ids = fields.Many2many("sale.order.line", string="Lignes à supprimer")
    
    @api.multi
    def di_supprimer_lignes(self):
        self.di_order_id.write({'order_line': [(2, line.id, False) for line in self.di_line_ids]}) 
       
    @api.model
    def default_get(self, fields):
        res = super(DiSuppLigZeroWiz, self).default_get(fields)         
                
        di_order_id = self.env['sale.order'].browse(self.env.context.get('active_id')) # la commande est sauvegardée quand on clique sur le bouton 
        
      
        if di_order_id.state=='draft':        
            di_line_ids= self.env['sale.order.line'].search(['&', ('order_id', '=', di_order_id.id), ('product_uom_qty', '=', 0.0)])
            
        liste_line_ids=[]
        for line in di_line_ids:
            liste_line_ids.append(line.id)            
        res['di_order_id']= di_order_id.id
        res['di_line_ids']=list(set(liste_line_ids)) # set permet de ne prendre que les valeurs uniques, et list pour reformater en liste
                                                    
        return res    